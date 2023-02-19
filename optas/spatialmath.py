import functools
import casadi as cs
from casadi import sin, cos, vec

"""

This is a partial port to Python/CasADi, with some modifications and
additions, of the Spatial Math Toolbox for MATLAB. See the following.


https://github.com/petercorke/spatialmath-matlab

"""

pi = cs.np.pi
eps = cs.np.finfo(float).eps


def arrayify_args(fun):
    """Decorator that ensures all input arguments are casadi arrays (i.e. either DM or SX)"""

    _arraylike_types = (cs.DM, cs.SX, list, tuple, cs.np.ndarray, float, int)

    def _handle_arraylike_args(args, handle):
        """Helper method that applies the handle to array like arguments."""
        args_out = []

        for a in args:
            if isinstance(a, _arraylike_types):
                args_out.append(handle(a))
            else:
                args_out.append(a)
        return args_out

    def _handle_arraylike_kwargs(kwargs, handle, default_kwargs):
        kwargs_out = {}

        for label, value in kwargs.items():
            if isinstance(value, _arraylike_types):
                kwargs_out[label] = handle(value)
            else:
                kwargs_out[label] = value

        for label, default_value in default_kwargs.items():
            if label not in kwargs_out and isinstance(default_value, _arraylike_types):
                kwargs_out[label] = handle(default_value)

        return kwargs_out

    @functools.wraps(fun)
    def wrap(*args, **kwargs):
        # Extract default values for kwargs from fun
        arg_names = fun.__code__.co_varnames[: fun.__code__.co_argcount]
        arg_defaults = fun.__defaults__
        if arg_defaults is not None:
            default_kwargs = dict(zip(arg_names[-len(arg_defaults) :], arg_defaults))
        else:
            default_kwargs = {}

        args_use = _handle_arraylike_args(args, cs.horzcat)
        kwargs_use = _handle_arraylike_kwargs(kwargs, cs.horzcat, default_kwargs)
        return fun(*args_use, **kwargs_use)

    return wrap


def I3():
    """3-by-3 identity matrix"""
    return cs.DM.eye(3)


def I4():
    """4-by-4 identity matrix"""
    return cs.DM.eye(4)


@arrayify_args
def angvec2r(theta, v):
    """Convert angle and vector orientation to a rotation matrix"""
    sk = skew(unit(v))
    R = I3() + sin(theta) * sk + (1.0 - cos(theta)) * sk @ sk  # Rodrigue's equation
    return R


@arrayify_args
def r2t(R):
    """Convert rotation matrix to a homogeneous transform"""
    return cs.vertcat(
        cs.horzcat(R, cs.DM.zeros(3)),
        cs.DM([[0.0, 0.0, 0.0, 1]]),
    )


@arrayify_args
def rotx(theta):
    """SO(3) rotation about X axis"""
    ct, st = cos(theta), sin(theta)
    return cs.vertcat(
        cs.DM([[1.0, 0.0, 0.0]]),
        cs.horzcat(0.0, ct, -st),
        cs.horzcat(0, st, ct),
    )


@arrayify_args
def roty(theta):
    """SO(3) rotation about Y axis"""
    ct, st = cos(theta), sin(theta)
    return cs.vertcat(
        cs.horzcat(ct, 0.0, st),
        cs.DM([[0.0, 1.0, 0.0]]),
        cs.horzcat(-st, 0.0, ct),
    )


@arrayify_args
def rotz(theta):
    """SO(3) rotation about Z axis"""
    ct, st = cos(theta), sin(theta)
    return cs.vertcat(
        cs.horzcat(ct, -st, 0.0),
        cs.horzcat(st, ct, 0.0),
        cs.DM([[0.0, 0.0, 1.0]]),
    )


@arrayify_args
def rpy2r(rpy, opt="zyx"):
    """Roll-pitch-yaw angles to SO(3) rotation matrix"""

    order = ["zyx", "xyz", "yxz", "arm", "vehicle", "camera"]
    r, p, y = cs.vertsplit(rpy)

    if opt in {"xyz", "arm"}:
        return rotx(y) @ roty(p) @ rotz(r)
    elif opt in {"zyx", "vehicle"}:
        return rotz(y) @ roty(p) @ rotx(r)
    elif opt in {"yxz", "camera"}:
        return roty(y) @ rotx(p) @ rotz(r)
    else:
        raise ValueError(f"didn't recognize given option {opt=}, only allowed {order}")


@arrayify_args
def rt2tr(R, t):
    """Convert rotation and translation to homogeneous transform"""
    return cs.vertcat(
        cs.horzcat(R, vec(t)),
        cs.DM([[0.0, 0.0, 0.0, 1.0]]),
    )


@arrayify_args
def skew(v):
    """Create skew-symmetric matrix"""
    if v.shape[0] == 1:
        return cs.vertcat(
            cs.horzcat(0.0, -v),
            cs.horzcat(v, 0.0),
        )
    elif v.shape[0] == 3:
        return cs.vertcat(
            cs.horzcat(0.0, -v[2], v[1]),
            cs.horzcat(v[2], 0.0, -v[0]),
            cs.horzcat(-v[1], v[0], 0.0),
        )
    else:
        raise ValueError(f"expecting a scalar or 3-vector")


@arrayify_args
def t2r(T):
    """Rotational submatrix"""
    return T[:3, :3]


@arrayify_args
def invt(T):
    """Inverse of a homogeneous transformation matrix"""
    R = t2r(T)
    t = transl(T)
    return rt2tr(R.T, -R.T @ t)


@arrayify_args
def transl(T):
    """SE(3) translational homogeneous transform"""
    return T[:3, 3]


@arrayify_args
def unit(v):
    """Unitize a vector"""
    return v / cs.norm_fro(v)


class Quaternion:

    """Quaternion class"""

    def __init__(self, x, y, z, w):
        """Quaternion constructor.

        Syntax
        ------

        quat = Quaternion(x, y, z, w)

        Parameters
        ----------

        x (number, array)
            Either the x-value of the quaternion or a 4-vector containing the quaternion.

        y (number)
            y-value of quaternion.

        z (number)
            z-value of quaternion.

        w (number)
            w-value of quaternion.

        """
        self._q = cs.vertcat(x, y, z, w)

    def split(self):
        """Split the quaternion into its xyzw parts."""
        return cs.vertsplit(self._q)

    def __mul__(self, quat):
        """Quaternion multiplication"""
        assert isinstance(quat, Quaternion), "unsupported type"
        x0, y0, z0, w0 = self.split()
        x1, y1, z1, w1 = quat.split()
        return Quaternion(
            x1 * w0 + y1 * z0 - z1 * y0 + w1 * x0,
            -x1 * z0 + y1 * w0 + z1 * x0 + w1 * y0,
            x1 * y0 - y1 * x0 + z1 * w0 + w1 * z0,
            -x1 * x0 - y1 * y0 - z1 * z0 + w1 * w0,
        )

    def sumsqr(self):
        """Sum the square values of the quaternion elements."""
        return cs.sumsqr(self._q)

    def inv(self):
        """Quaternion inverse"""
        q = self.getquat()
        qinv = cs.vertcat(-q[:3], q[3]) / self.sumsqr()
        return Quaternion(qinv[0], qinv[1], qinv[2], qinv[3])

    @staticmethod
    def fromrpy(rpy):
        """Return a quaternion from Roll-Pitch-Yaw angles."""

        r, p, y = cs.vertsplit(vec(rpy))
        cr, sr = cs.cos(0.5 * r), cs.sin(0.5 * r)
        cp, sp = cs.cos(0.5 * p), cs.sin(0.5 * p)
        cy, sy = cs.cos(0.5 * y), cs.sin(0.5 * y)

        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy
        w = cr * cp * cy + sr * sp * sy

        n = cs.sqrt(x * x + y * y + z * z + w * w)
        return Quaternion(x / n, y / n, z / n, w / n)

    @staticmethod
    def fromangvec(theta, v):
        """Return a quaternion from angle-vector form."""
        w = cos(0.5 * theta)
        xyz = sin(0.5 * theta) * unit(vec(v))
        x, y, z = cs.vertsplit(xyz)
        return Quaternion(x, y, z, w)

    def getquat(self):
        """Return the quaternion vector."""
        return self._q

    def getrpy(self):
        """Return the quaternion as Roll-Pitch-Yaw angles."""
        qx, qy, qz, qw = self.split()

        sinr_cosp = 2.0 * (qw * qx + qy * qz)
        cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
        roll = cs.atan2(sinr_cosp, cosr_cosp)

        sinp = 2.0 * (qw * qy - qz * qx)

        pitch = cs.if_else(cs.fabs(sinp) >= 1.0, pi / 2.0, cs.asin(sinp))

        siny_cosp = 2.0 * (qw * qz + qx * qy)
        cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)

        yaw = cs.atan2(siny_cosp, cosy_cosp)

        return cs.vertcat(roll, pitch, yaw)
