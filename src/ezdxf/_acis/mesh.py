#  Copyright (c) 2022, Manfred Moitzi
#  License: MIT License
from typing import List, Iterator, Sequence, Optional
from ezdxf.acis import ParsingError
from ezdxf._acis.entities import Body, Lump
from ezdxf.render import MeshVertexMerger, MeshTransformer
from ezdxf.math import Matrix44, Vec3


def from_body(body: Body, merge_lumps=True) -> List[MeshTransformer]:
    """Returns a list of :class:`~ezdxf.render.MeshTransformer` instances from
    the given ACIS :class:`~ezdxf.acis.entities.Body` entity.
    The list contains multiple meshes if `merge_lumps` is ``False`` or just a
    singe mesh if `merge_lumps` is ``True``.

    This function returns only meshes build up by planar polygonal faces stored
    in a :class:`~ezdxf.acis.entities.Body` entity, for a conversion of more
    complex ACIS data structures is an ACIS kernel required.

    Args:
        body: ACIS entity of type :class:`~ezdxf.acis.entities.Body`
        merge_lumps: returns all :class:`Lump` entities
            from a body as a single mesh if ``True`` otherwise each :class:`Lump`
            entity is a separated mesh

    Raises:
        TypeError: given `body` entity has invalid type

    """
    if not isinstance(body, Body):
        raise TypeError(f"expected body, got: {type(body)}")

    meshes: List[MeshTransformer] = []
    builder = MeshVertexMerger()
    for faces in flat_polygon_faces_from_body(body):
        for face in faces:
            builder.add_face(face)
        if not merge_lumps:
            meshes.append(MeshTransformer.from_builder(builder))
            builder = MeshVertexMerger()
    if merge_lumps:
        meshes.append(MeshTransformer.from_builder(builder))
    return meshes


def flat_polygon_faces_from_body(
    body: Body,
) -> Iterator[List[Sequence[Vec3]]]:
    """Yields all flat polygon faces from all lumps in the given
    :class:`~ezdxf.acis.entities.Body` entity.
    Yields a separated list of faces for each linked :class:`Lump` entity.

    Args:
        body: ACIS entity of type :class:`~ezdxf.acis.entities.Body`

    Raises:
        TypeError: given `body` entity has invalid type

    """

    if not isinstance(body, Body):
        raise TypeError(f"expected body, got: {type(body)}")
    lump = body.lump
    transform = body.transform

    m: Optional[Matrix44] = None
    if not transform.is_none:
        m = transform.matrix
    while not lump.is_none:
        yield list(flat_polygon_faces_from_lump(lump, m))
        lump = lump.next_lump


def flat_polygon_faces_from_lump(
    lump: Lump, m: Matrix44 = None
) -> Iterator[Sequence[Vec3]]:
    """Yields all flat polygon faces from the given :class:`Lump` entity as
    sequence  of :class:`~ezdxf.math.Vec3` instances. Applies the transformation
    :class:`~ezdxf.math.Matrix44` `m` to all vertices if not ``None``.

    Args:
        lump: ACIS raw entity of type `lump`_
        m: optional transformation matrix

    Raises:
        TypeError: `lump` has invalid ACIS type

    """
    if not isinstance(lump, Lump):
        raise TypeError(f"expected body, got: {type(lump)}")

    shell = lump.shell
    if shell.is_none:
        return  # not a shell
    vertices: List[Vec3] = []
    face = shell.face
    while not face.is_none:
        vertices.clear()
        if face.surface.type != "plane-surface":
            continue  # not a plane-surface or a polygon face
        try:
            first_coedge = face.loop.coedge
        except AttributeError:  # loop is none entity
            continue
        if first_coedge.is_none:
            continue  # don't know what is going on

        coedge = first_coedge
        while True:
            # the edge entity contains the vertices and the curve type
            edge = coedge.edge
            if edge.is_none:
                break
            # only straight lines as face edges supported:
            if edge.curve.type != "straight-curve":
                break
            try:
                vertices.append(edge.start_vertex.point.location)
            except AttributeError:
                break
            coedge = coedge.next_coedge
            if coedge.is_none:  # not a closed face
                break
            if coedge is first_coedge:  # a valid closed face
                if m is not None:
                    yield tuple(m.transform_vertices(vertices))
                else:
                    yield tuple(vertices)
                break

        face = face.next_face
