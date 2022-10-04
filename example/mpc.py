# Python standard lib
import os
import sys
import math
import pathlib

# PyBullet
import pybullet_api

# OpTaS
import optas
from optas.spatialmath import *


######################################
# Task space planner and controller
#
# This is an implementation of [1].
#
# References
#
#   1. J. Moura, T. Stouraitis, and S. Vijayakumar, Non-prehensile
#      Planar Manipulation via Trajectory Optimization with
#      Complementarity Constraints, ICRA, 2022.
#

class TOMPCCPlanner:

    def __init__(self, dt, Lx, Ly):

        # Setup
        mu = 0.1  # coef of friction
        dt = float(dt)  # time step
        nX = 4  # number of state variables
        nU = 4  # number of control variables
        T = 20  # number of step
        Lx = float(Lx)  # length of slider (box) in x-axis
        Ly = float(Ly)  # length of slider (box) in y-axis
        phi_lo = -math.atan2(Ly, Lx)  # lower limit for phi
        phi_up = -math.pi + abs(phi_lo) # upper limit for phi
        L = optas.diag([1, 1, 0.5])  # limit surface model
        SxC0 = 0.      # initial contact position in x-axis of slider
        SyC0 = -0.5*Ly # initial contact position in y-axis of slider
        SphiC0 = -0.5*optas.np.pi # initial contact orientation in slider frame
        Wu = optas.diag([ # weigting on minimizing controls cost term
            1.,  # normal contact force
            1.,  # tangential contact force
            1.,  # angular rate of sliding, positive part
            1.,  # angular rate of sliding, negative part
        ])
        WxT = optas.diag([ # weighting for terminal state cost term
            1000., # x-position of slider
            1000., # y-position of slider
            1., # orientation of slider
            1., # orientation of contact
        ])
        we = 0.1  # slack weights
        SphiCT = 0.  # final contact orientation in slider frame

        # Setup task models
        state = optas.TaskModel('state', dim=nX, time_derivs=[0])
        control = optas.TaskModel('control', dim=nU, time_derivs=[0], T=T-1, symbol='u')

        # Setup optimization builder
        builder = optas.OptimizationBuilder(T=T, tasks=[state, control])

        # Add additional decision variables
        eps = builder.add_decision_variables('slack', T-1)

        # Set parameters
        GpS0 = builder.add_parameter('GpS0', 2)  # initial slider position in global frame
        GthetaS0 = builder.add_parameter('GthetaS0') # initial slider orientation in global frame
        GpST = builder.add_parameter('GpST', 2)  # goal slider position in global frame
        GthetaST = builder.add_parameter('GthetaST') # goal slider orientation in global frame

        # Get states/controls
        X = builder.get_model_states('state')
        U = builder.get_model_states('control')

        # Constraint: initial configuration
        x0 = optas.vertcat(GpS0, GthetaS0, SphiC0)
        builder.initial_configuration('state', x0)

        # Split X/U
        theta = X[2,:]
        phi = X[3, :]

        fn = U[0,:]
        ft = U[1,:]
        dphip = U[2,:]
        dphim = U[3,:]

        # Constraint: dynamics
        o2 = optas.DM.zeros(2)  # 2-vector of zeros
        o3 = optas.DM.zeros(3)  # 3-vector of zeros
        I = optas.DM.eye(2)  # 2-by-2 identity
        for k in range(T-1):

            # Setup
            xn = X[:, k+1]  # next state
            x = X[:, k]   # current state
            u = U[:, k]  # control input
            R = rotz(theta[k])  # rotation matrix in xy-plane of slider
            SyC = -0.5*Ly  # y-position of contact
            SxC = SyC/optas.tan(phi[k])  # x-position of box
            JC = optas.horzcat(I, optas.vertcat(-SyC, SxC))

            # Compute system dynamics f(x, u) = Ku
            K = optas.vertcat(
                optas.horzcat(R @ L @ JC.T, o3, o3),
                optas.horzcat(o2.T, 1, -1),
            )
            f = K @ u

            # Add constraint
            builder.add_equality_constraint(f'dynamics_{k}', xn, x + dt*f)

        # Constraint: complementarity
        lambda_minus = mu*fn - ft
        lambda_plus = mu*fn + ft
        lambda_v = optas.vertcat(lambda_minus, lambda_plus)
        dphi_v = optas.vertcat(dphip, dphim)

        builder.add_geq_inequality_constraint('positive_lambda_v', lambda_v)
        builder.add_geq_inequality_constraint('positive_dphi_v', dphi_v)

        for k in range(T-1):
            e = eps[k]
            lambda_vk = lambda_v[:, k]
            dphi_vk = dphi_v[:, k]
            builder.add_equality_constraint(
                f'complementarity_{k}', lambda_vk.T@dphi_vk + e,
            )

        # Cost: minimize control magnitude
        for k in range(T-1):
            u = U[:, k]
            builder.add_cost_term(f'min_control_{k}', u.T @ Wu @ u)

        # Cost: terminal state
        xT = optas.vertcat(GpST, GthetaST, SphiCT)
        xbarT = X[:, -1] - xT
        builder.add_cost_term('terminal_state', xbarT.T @ WxT @ xbarT)

        # Cost: slack terms
        builder.add_cost_term('slack', we*cs.sumsqr(eps))

        # Constraint: slack
        builder.add_geq_inequality_constraint('positive_slack', eps)

        # Constraint: bound phi
        builder.add_bound_inequality_constraint('phi_bound', phi_lo, phi, phi_up)
        
        # Setup solver
        opt = builder.build()
        self.solver = optas.CasADiSolver(opt).setup('ipopt')
        # self.solver = optas.ScipyMinimizeSolver(opt).setup('SLSQP')

        # For later
        self.Tmax = float(T-1)*dt
        self.T = T
        self.nX = nX

    def plan(self, GpS0, GthetaS0, GpST, GthetaST):


        state_x_init = optas.DM.zeros(self.nX, self.T)
        
        for k in range(self.T):
            alpha = float(k)/float(self.T-1)
            state_x_init[:2,k] = optas.DM(GpS0) * (1-alpha) + alpha*optas.DM(GpST)
            state_x_init[2, k] = GthetaS0 * (1-alpha) + alpha * GthetaST
        self.solver.reset_initial_seed({'state/x': state_x_init})
        
        self.solver.reset_parameters({
            'GpS0': GpS0,
            'GthetaS0': GthetaS0,
            'GpST': GpST,
            'GthetaST': GthetaST,
        })

        solution = self.solver.solve()
        from pprint import pprint
        pprint(solution)
        slider_traj = solution['state/x'][:3, :]
        slider_plan = self.solver.interpolate(slider_traj, self.Tmax)
        return slider_plan

class TOMPCCController:

    def __init__(self):
        pass

    def compute_target_velocity(self):
        pass


######################################
# Joint space IK
#


class IK:

    def __init__(self, dt, thresh_angle):

        cwd = pathlib.Path(__file__).parent.resolve() # path to current working directory
        pi = optas.np.pi  # 3.141...
        T = 1 # no. time steps in trajectory
        link_ee = 'end_effector_ball'  # end-effector link name

        # Setup robot
        urdf_filename = os.path.join(cwd, 'robots', 'kuka_lwr.urdf')
        kuka = optas.RobotModel(
            urdf_filename=urdf_filename,
            time_derivs=[1],  # i.e. joint velocity
        )
        kuka_name = kuka.get_name()

        # Setup optimization builder
        builder = optas.OptimizationBuilder(T=T, robots=[kuka], derivs_align=True)

        # Setup parameters
        qc = builder.add_parameter('qc', kuka.ndof)  # current robot joint configuration
        pg = builder.add_parameter('pg', 3)  # goal end-effector position

        # Get joint velocity
        dq = builder.get_model_state(kuka_name, t=0, time_deriv=1)

        # Get next joint state
        q = qc + dt*dq

        # Get jacobian
        Jl = kuka.get_global_linear_geometric_jacobian(link_ee, qc)

        # Get end-effector velocity
        dp = Jl @ dq

        # Get current end-effector position
        pc = kuka.get_global_link_position(link_ee, qc)

        # Get next end-effector position
        p = pc + dt*dp

        # Cost: match end-effector position
        diffp = p - pg
        W_p = optas.diag([20., 20., 1.])
        builder.add_cost_term('match_p', diffp.T @ W_p @ diffp)

        # Cost: min joint velocity
        w_dq = 0.01
        builder.add_cost_term('min_dq', w_dq*optas.sumsqr(dq))

        # Get global z-axis of end-effector
        T = kuka.get_global_link_transform(link_ee, q)
        z = T[:3, 2]

        # Constraint: eff orientation
        e = optas.DM([0, 0, -1.])
        builder.add_leq_inequality_constraint('eff_orien', optas.cos(thresh_angle), e.T @ z)

        # Cost: align eff
        w_ori = 10.
        builder.add_cost_term('eff_orien', w_ori*optas.sumsqr(e.T @ z - 1))

        # Setup solver
        optimization = builder.build()
        self.solver = optas.CasADiSolver(optimization).setup('sqpmethod')

        # Setup variables required later
        self.kuka_name = kuka_name

    def compute_target_velocity(self, qc, pg):
        self.solver.reset_parameters({'qc': optas.DM(qc), 'pg': optas.DM(pg)})
        solution = self.solver.solve()
        return solution[f'{self.kuka_name}/dq'].toarray().flatten()

def main():

    # Setup PyBullet
    qc = -optas.np.deg2rad([0, 30, 0, -90, 0, 60, 0])
    q = qc.copy()
    hz = 50
    dt = 1.0/float(hz)
    pb = pybullet_api.PyBullet(dt)
    kuka = pybullet_api.Kuka()
    kuka.reset(qc)
    GxS0 = 0.4
    GyS0 = 0.065
    GthetaS0 = 0.
    box_base_position = [GxS0, GyS0, 0.06]
    Lx = 0.2
    Ly = 0.1
    box_half_extents = [0.5*Lx, 0.5*Ly, 0.06]
    box = pybullet_api.DynamicBox(
        base_position=box_base_position,
        half_extents=box_half_extents,
    )
    GxST = 0.4
    GyST = 0.2
    GthetaST = 0.
    pybullet_api.VisualBox(
        base_position=[GxST, GyST, 0.06],
        half_extents=box_half_extents,
        rgba_color=[1., 0., 0., 0.5],
    )

    # Setup TO MPCC planner
    to_mpcc_planner = TOMPCCPlanner(0.1, Lx, Ly)

    # Setup TO MPCC controller
    to_mpcc_controller = TOMPCCController()

    # Setup IK
    thresh_angle = optas.np.deg2rad(30.)
    ik = IK(dt, thresh_angle)

    # Start pybullet
    pb.start()
    start_time = pybullet_api.time.time()

    # Move robot to start position
    Tmax_start = 6.
    pginit = optas.np.array([0.4, 0., 0.06])
    while False:  # >>>>>>>>>>TEMP<<<<<<<<<<<
        t = pybullet_api.time.time() - start_time
        if t > Tmax_start:
            break
        dqgoal = ik.compute_target_velocity(q, pginit)
        q += dt*dqgoal
        kuka.cmd(q)
        pybullet_api.time.sleep(dt)

    # Plan a trajectory
    GpS0 = [GxS0, GyS0]
    GpST = [GxST, GyST]
    plan = to_mpcc_planner.plan(GpS0, GthetaS0, GpST, GthetaST)
    sys.exit(0)

    # Main loop
    p = pginit.copy()
    start_time = pybullet_api.time.time()
    while True:
        t = pybullet_api.time.time() - start_time
        boxpose = box.get_pose()
        dqgoal = ik.compute_target_velocity(q, p)
        q += dt*dqgoal
        kuka.cmd(q)
        pybullet_api.time.sleep(dt)

    pb.stop()
    pb.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
