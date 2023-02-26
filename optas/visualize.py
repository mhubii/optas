import os

import vtk
from vtkmodules.vtkFiltersSources import (
    vtkCylinderSource,
    vtkSphereSource,
    vtkCubeSource,
)

import casadi as cs
import numpy as np
from scipy.spatial.transform import Rotation as Rot

from urdf_parser_py.urdf import Mesh, Cylinder, Sphere

from .spatialmath import *


def line(
    start=[0.0, 0.0, 0.0], end=[1.0, 0.0, 0.0], rgb=None, alpha=1.0, linewidth=1.0
):
    points = vtk.vtkPoints()
    points.InsertNextPoint(*start)
    points.InsertNextPoint(*end)

    line = vtk.vtkLine()
    line.GetPointIds().SetId(0, 0)
    line.GetPointIds().SetId(0, 1)

    lines = vtk.vtkCellArray()
    lines.InsertNextCell(line)

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetLines(lines)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polydata)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    actor.GetProperty().SetLineWidth(linewidth)

    if isinstance(rgb, list):
        assert len(rgb) == 3, f"rgb is incorrect length, got {len(rgb)} expected 3"
        actor.GetProperty().SetColor(*rgb)

    if alpha < 1.0:
        assert alpha >= 0.0, "the scalar alpha must be in the range [0, 1]"
        actor.GetProperty().SetOpacity(alpha)

    return actor


def sphere(
    radius=1.0,
    position=[0.0, 0.0, 0.0],
    rgb=None,
    alpha=1.0,
    theta_resolution=20,
    phi_resolution=20,
):
    sphere = vtkSphereSource()
    sphere.SetRadius(radius)
    sphere.SetThetaResolution(theta_resolution)
    sphere.SetPhiResolution(phi_resolution)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(sphere.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    if isinstance(position, list):
        transform = vtk.vtkTransform()
        transform.Translate(position)
        actor.SetUserTransform(transform)

    if isinstance(rgb, list):
        assert len(rgb) == 3, f"rgb is incorrect length, got {len(rgb)} expected 3"
        actor.GetProperty().SetColor(*rgb)

    if alpha < 1.0:
        assert alpha >= 0.0, "the scalar alpha must be in the range [0, 1]"
        actor.GetProperty().SetOpacity(alpha)

    return actor


def box(
    scale=[1, 1, 1],
    rgb=None,
    alpha=1.0,
    position=[0.0, 0.0, 0.0],
    orientation=[0.0, 0.0, 0.0],
    euler_seq="xyz",
    euler_degrees=False,
):
    cube = vtk.vtkCubeSource()
    cube.SetBounds(
        -0.5 * scale[0],
        0.5 * scale[0],
        -0.5 * scale[1],
        0.5 * scale[1],
        -0.5 * scale[2],
        0.5 * scale[2],
    )

    # Create a vtkPolyDataMapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cube.GetOutputPort())

    # Create a vtkActor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    if len(orientation) == 4:
        R = Rot.from_quat(orientation)
    elif len(orientation) == 3:
        R = Rot.from_euler(euler_seq, orientation, degrees=euler_degrees)
    else:
        raise ValueError(
            f"length for orientation is incorrect, expected 3 or 4, got {len(orientation)}"
        )

    tf = np.eye(4)
    tf[:3, :3] = R.as_matrix()
    tf[:3, 3] = position

    transform = vtk.vtkTransform()
    transform.SetMatrix(tf.flatten().tolist())
    actor.SetUserTransform(transform)

    if isinstance(rgb, list):
        assert len(rgb) == 3, f"rgb is incorrect length, got {len(rgb)} expected 3"
        actor.GetProperty().SetColor(*rgb)

    if alpha < 1.0:
        assert alpha >= 0.0, "the scalar alpha must be in the range [0, 1]"
        actor.GetProperty().SetOpacity(alpha)

    return actor


def cylinder(
    radius=1.0,
    height=1.0,
    rgb=None,
    alpha=1.0,
    resolution=20,
    position=[0.0, 0.0, 0.0],
    orientation=[0.0, 0.0, 0.0],
    euler_seq="xyz",
    euler_degrees=False,
):
    cylinder = vtkCylinderSource()
    cylinder.SetRadius(radius)
    cylinder.SetHeight(height)
    cylinder.SetResolution(resolution)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cylinder.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    if len(orientation) == 4:
        R = Rot.from_quat(orientation)
    elif len(orientation) == 3:
        R = Rot.from_euler(euler_seq, orientation, degrees=euler_degrees)
    else:
        raise ValueError(
            f"length for orientation is incorrect, expected 3 or 4, got {len(orientation)}"
        )

    tf = np.eye(4)
    tf[:3, :3] = R.as_matrix()
    tf[:3, 3] = position

    transform = vtk.vtkTransform()
    transform.SetMatrix(tf.flatten().tolist())
    actor.SetUserTransform(transform)

    if isinstance(rgb, list):
        assert len(rgb) == 3, f"rgb is incorrect length, got {len(rgb)} expected 3"
        actor.GetProperty().SetColor(*rgb)

    if alpha < 1.0:
        assert alpha >= 0.0, "the scalar alpha must be in the range [0, 1]"
        actor.GetProperty().SetOpacity(alpha)

    return actor


def cylinder_urdf(
    radius=1.0,
    height=1.0,
    rgb=None,
    alpha=1.0,
    resolution=20,
    position=[0.0, 0.0, 0.0],
    orientation=[0.0, 0.0, 0.0],
    euler_seq="xyz",
    euler_degrees=False,
):
    cylinder = vtkCylinderSource()
    cylinder.SetRadius(radius)
    cylinder.SetHeight(height)
    cylinder.SetResolution(resolution)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cylinder.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    if len(orientation) == 4:
        R = Rot.from_quat(orientation)
    elif len(orientation) == 3:
        R = Rot.from_euler(euler_seq, orientation, degrees=euler_degrees)
    else:
        raise ValueError(
            f"length for orientation is incorrect, expected 3 or 4, got {len(orientation)}"
        )

    tf_0 = np.eye(4)
    tf_0[:3, :3] = Rot.from_euler("x", 90, degrees=True).as_matrix()

    tf_1 = np.eye(4)
    tf_1[:3, :3] = R.as_matrix()
    tf_1[:3, 3] = position

    tf = tf_1 @ tf_0

    transform = vtk.vtkTransform()
    transform.SetMatrix(tf.flatten().tolist())
    actor.SetUserTransform(transform)

    if isinstance(rgb, list):
        assert len(rgb) == 3, f"rgb is incorrect length, got {len(rgb)} expected 3"
        actor.GetProperty().SetColor(*rgb)

    if alpha < 1.0:
        assert alpha >= 0.0, "the scalar alpha must be in the range [0, 1]"
        actor.GetProperty().SetOpacity(alpha)

    return actor


def text(
    camera,
    text="Hello, world!",
    position=[0.0, 0.0, 0.0],
    scale=[1.0, 1.0, 1.0],
    rgb=None,
    alpha=1.0,
):
    # Create a text source to generate the text
    textSource = vtk.vtkTextSource()
    textSource.SetText(text)
    textSource.Update()

    # Create a mapper to map the text source to graphics primitives
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(textSource.GetOutputPort())

    # Create a follower to position the text in 3D space
    follower = vtk.vtkFollower()
    follower.SetMapper(mapper)
    follower.SetPosition(*position)
    follower.SetScale(*scale)
    follower.GetProperty().SetOpacity(alpha)
    follower.SetCamera(camera)

    return follower


def link(
    T=None,
    axis_scale=0.1,
    axis_linewidth=1.0,
    center_radius=0.01,
    center_rgb=None,
    center_alpha=1.0,
):
    if T is None:
        T = np.eye(4)

    p = T[:3, 3].flatten()
    x = T[:3, 0].flatten()
    y = T[:3, 1].flatten()
    z = T[:3, 2].flatten()

    actors = []

    actors.append(
        line(
            start=p.tolist(),
            end=(p + axis_scale * x).tolist(),
            rgb=[1, 0, 0],
            linewidth=axis_linewidth,
        )
    )

    actors.append(
        line(
            start=p.tolist(),
            end=(p + axis_scale * y).tolist(),
            rgb=[0, 1, 0],
            linewidth=axis_linewidth,
        )
    )

    actors.append(
        line(
            start=p.tolist(),
            end=(p + axis_scale * z).tolist(),
            rgb=[0, 0, 1],
            linewidth=axis_linewidth,
        )
    )

    actors.append(
        sphere(
            radius=center_radius,
            position=p,
            rgb=center_rgb,
            alpha=center_alpha,
        )
    )

    return actors


def grid_floor(
    num_cells=10,
    rgb=None,
    alpha=1.0,
    linewidth=3.0,
    inner_rgb=None,
    inner_alpha=None,
    inner_linewidth=1.0,
    stride=1.0,
    euler=[0, 0, 0],
    euler_degrees=True,
):
    assert num_cells > 0, "num_cells must be a positive number!"
    assert num_cells % 2 == 0, "num_cells must be even!"

    actors = []

    num_lines = num_cells + 1

    tf_0 = np.eye(4)
    tf_0[:3, 3] = [
        -0.5 * float(num_cells) * stride,
        -0.5 * float(num_cells) * stride,
        0,
    ]

    tf_1 = np.eye(4)
    tf_1[:3, :3] = Rot.from_euler("xyz", euler, degrees=euler_degrees).as_matrix()

    tf = tf_1 @ tf_0

    offset = vtk.vtkTransform()
    offset.SetMatrix(tf.flatten().tolist())

    if inner_rgb is None:
        inner_rgb = rgb

    if inner_alpha is None:
        inner_alpha = alpha

    for i in range(num_cells):
        actor = line(
            start=[(float(i) + 0.5) * stride, 0, 0],
            end=[(float(i) + 0.5) * stride, float(num_cells) * stride, 0],
            linewidth=inner_linewidth,
            alpha=inner_alpha,
            rgb=inner_rgb,
        )
        actor.SetUserTransform(offset)
        actors.append(actor)

        actor = line(
            start=[0, (float(i) + 0.5) * stride, 0],
            end=[float(num_cells) * stride, (float(i) + 0.5) * stride, 0],
            linewidth=inner_linewidth,
            alpha=inner_alpha,
            rgb=inner_rgb,
        )
        actor.SetUserTransform(offset)
        actors.append(actor)

    for i in range(num_lines):
        actor = line(
            start=[float(i) * stride, 0, 0],
            end=[float(i) * stride, float(num_cells) * stride, 0],
            rgb=rgb,
            alpha=alpha,
            linewidth=linewidth,
        )
        actor.SetUserTransform(offset)
        actors.append(actor)

        actor = line(
            start=[0, float(i) * stride, 0],
            end=[float(num_cells) * stride, float(i) * stride, 0],
            rgb=rgb,
            alpha=alpha,
            linewidth=linewidth,
        )
        actor.SetUserTransform(offset)
        actors.append(actor)

    return actors


def obj(
    obj_filename,
    png_texture_filename=None,
    position=[0.0, 0.0, 0.0],
    orientation=[0.0, 0.0, 0.0],
    euler_seq="xyz",
    euler_degrees=False,
):
    # Create a renderer, render window, and interactor
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)

    # Read the .obj file
    reader = vtk.vtkOBJReader()
    reader.SetFileName(obj_filename)
    reader.Update()

    # Create a mapper and actor
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    if isinstance(png_texture_filename, str):
        # Create a texture from the png file
        texture = vtk.vtkTexture()
        texture_image = vtk.vtkPNGReader()
        texture_image.SetFileName(png_texture_filename)
        texture_image.Update()
        texture.SetInputConnection(texture_image.GetOutputPort())

        actor.SetTexture(texture)

    if len(orientation) == 4:
        R = Rot.from_quat(orientation)
    elif len(orientation) == 3:
        R = Rot.from_euler(euler_seq, orientation, degrees=euler_degrees)
    else:
        raise ValueError(
            f"length for orientation is incorrect, expected 3 or 4, got {len(orientation)}"
        )

    tf = np.eye(4)
    tf[:3, :3] = R.as_matrix()
    tf[:3, 3] = position

    transform = vtk.vtkTransform()
    transform.SetMatrix(tf.flatten().tolist())
    actor.SetUserTransform(transform)

    return actor


def stl(
    filename,
    scale=None,
    rgb=None,
    alpha=1.0,
    position=[0.0, 0.0, 0.0],
    orientation=[0.0, 0.0, 0.0],
    euler_seq="xyz",
    euler_degrees=False,
):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(filename)

    if scale is None:
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
    else:
        transform = vtk.vtkTransform()
        transform.Scale(*scale)

        transformFilter = vtk.vtkTransformPolyDataFilter()
        transformFilter.SetTransform(transform)
        transformFilter.SetInputConnection(reader.GetOutputPort())

        # Visualize the object
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(transformFilter.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

    if len(orientation) == 4:
        R = Rot.from_quat(orientation)
    elif len(orientation) == 3:
        R = Rot.from_euler(euler_seq, orientation, degrees=euler_degrees)
    else:
        raise ValueError(
            f"length for orientation is incorrect, expected 3 or 4, got {len(orientation)}"
        )

    tf = np.eye(4)
    tf[:3, :3] = R.as_matrix()
    tf[:3, 3] = np.array(position).flatten()

    transform = vtk.vtkTransform()
    transform.SetMatrix(tf.flatten().tolist())
    actor.SetUserTransform(transform)

    if isinstance(rgb, list):
        assert len(rgb) == 3, f"rgb is incorrect length, got {len(rgb)} expected 3"
        actor.GetProperty().SetColor(*rgb)

    if alpha < 1.0:
        assert alpha >= 0.0, "the scalar alpha must be in the range [0, 1]"
        actor.GetProperty().SetOpacity(alpha)

    return actor


def robot(robot_model, q=None, alpha=1.0):
    actors = []

    urdf = robot_model.get_urdf()

    material_names = [m.name for m in urdf.materials]

    def get_material_rgba(name):
        try:
            idx = material_names.index(name)
        except ValueError:
            return None
        material = urdf.materials[idx]
        if material.color is not None:
            return material.color.rgba

    if q is None:
        q_user_input = [0.0] * robot_model.ndof
    else:
        q_user_input = cs.vec(q)

    # Setup functions to compute visual origins in global frame
    q = cs.SX.sym("q", robot_model.ndof)
    link_tf = {}
    visual_tf = {}
    for link in urdf.links:
        name = link.name

        lnk_tf = robot_model.get_global_link_transform(link.name, q)
        link_tf[name] = cs.Function(f"link_tf_{name}", [q], [lnk_tf])

        xyz, rpy = robot_model.get_link_visual_origin(link)
        visl_tf = rt2tr(rpy2r(rpy), xyz)

        tf = lnk_tf @ visl_tf
        visual_tf[name] = cs.Function(f"visual_tf_{name}", [q], [tf])

    for link in urdf.links:
        if link.visual is None:
            continue

        geometry = link.visual.geometry
        tf = visual_tf[link.name](q_user_input).toarray()
        position = tf[:3, 3].flatten().tolist()
        orientation = Rot.from_matrix(tf[:3, :3]).as_quat().tolist()

        material = link.visual.material
        rgb = None
        if isinstance(material.name, str) and material.name in material_names:
            rgba = get_material_rgba(link.visual.material.name)
            rgb = rgba[:3]

        if isinstance(geometry, Mesh):
            if geometry.filename.lower().endswith(".stl"):
                filename = geometry.filename

                if not os.path.exists(filename):
                    relpath = robot_model.get_urdf_dirname()
                    filename = os.path.join(relpath, filename)

                scale = None
                if geometry.scale is not None:
                    scale = geometry.scale

                actors.append(
                    stl(
                        filename,
                        scale=scale,
                        position=position,
                        orientation=orientation,
                        alpha=alpha,
                        rgb=rgb,
                    )
                )

        elif isinstance(geometry, Sphere):
            actors.append(
                sphere(
                    radius=geometry.radius,
                    rgb=rgb,
                    position=position,
                    alpha=alpha,
                )
            )

        elif isinstance(geometry, Cylinder):
            actors.append(
                cylinder_urdf(
                    radius=geometry.radius,
                    height=geometry.length,
                    position=position,
                    orientation=orientation,
                    rgb=rgb,
                    alpha=alpha,
                )
            )

    return actors


def robot_traj(robot_model, Q, alpha_spec=None):
    default_alpha_spec = {"style": "A"}
    if alpha_spec is None:
        alpha_spec = default_alpha_spec.copy()

    actors = []
    n = Q.shape[1]

    if alpha_spec["style"] == "A":
        alpha_min = alpha_spec.get("alpha_min", 0.1)
        alpha_max = alpha_spec.get("alpha_max", 1.0)
        alphas = np.linspace(alpha_min, alpha_max, n).tolist()
    elif alpha_spec["style"] == "B":
        alpha_min = alpha_spec.get("alpha_min", 0.1)
        alpha_max = alpha_spec.get("alpha_max", 1.0)
        alphas = [alpha_min] * (n - 1) + [alpha_max]
    elif alpha_spec["style"] == "C":
        alpha_start = alpha_spec.get("alpha_start", 1.0)
        alpha_mid = alpha_spec.get("alpha_mid", 0.1)
        alpha_end = alpha_spec.get("alpha_end", 1.0)
        alphas = [alpha_start] + [alpha_mid] * (n - 2) + [alpha_end]

    for i, alpha in enumerate(alphas):
        actors += robot(robot_model, q=Q[:, i], alpha=alpha)
    return actors


class Visualizer:
    def __init__(
        self,
        window_size=[1440, 810],
        background_color=[0, 0, 0],
        camera_position=[2, 2, 2],
        camera_focal_point=[0, 0, 0],
        camera_view_up=[0, 0, 1],
    ):
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(*background_color)
        self.renWin = vtk.vtkRenderWindow()
        self.renWin.AddRenderer(self.ren)
        self.renWin.SetSize(int(window_size[0]), int(window_size[1]))

        self.camera = self.ren.GetActiveCamera()
        self.camera.SetPosition(*camera_position)
        self.camera.SetFocalPoint(*camera_focal_point)
        self.camera.SetViewUp(*camera_view_up)

        self.iren = vtk.vtkRenderWindowInteractor()
        self.iren.SetRenderWindow(self.renWin)

        style = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(style)

        self.actors = []

    def append_actors(self, *actors):
        for actor in actors:
            if isinstance(actor, list):
                self.actors += actor  # assume actor is a list of actors
            else:
                self.actors.append(actor)  # assume actor is a single actor

    def start(self):
        for actor in self.actors:
            self.ren.AddActor(actor)
        self.iren.Initialize()
        self.renWin.Render()
        self.iren.Start()
