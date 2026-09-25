bl_info = {
    "name": "Parts and Sizes Calculator",
    "author": "AnimusPEXUS",
    "version": (0, 1),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Parts Calculator",
    "description": "Calculates parts, sizes and counts",
    "category": "3D View",
}

import bpy
import decimal
import mathutils

print_debug_messages = False
print_debug_messages_get_minmax_xyz_in_coords = False


class WRO_PAS_A_calc_all(bpy.types.Operator):
    bl_idname = "wro_pas_a.calc_all"
    bl_label = "Calculate"
    # bl_description = "no descr"

    def execute(self, context):
        topics_text = bpy.context.scene.wro_pas_a_config.topics
        topics = topics_text.splitlines()

        for i in range(len(topics)-1, -1, -1):
            s = topics[i].strip()
            if len(s) == 0:
                del topics[i]
            else:
                topics[i] = s

        topics_text = '\n'.join(topics) + '\n'

        # bpy.context.scene.wro_pas_a_config.selected_object

        wobj = None
        if (
            bpy.context.scene.wro_pas_a_config.within_selected_object_imaginable_box
            and bpy.context.scene.wro_pas_a_config.selected_object
        ):
            wobj = bpy.context.scene.wro_pas_a_config.selected_object

        objs = get_objects(
            topics,
            bpy.context.scene.wro_pas_a_config.among_selected,
            wobj,
            bpy.context.scene.wro_pas_a_config.allow_partial
        )

        calc_result = calc_pices(objs, topics)

        calc_result_text = calc_pices_res_repr(calc_result)

        a = bpy.data.texts.new('report')

        a.write(calc_result_text)

        bpy.context.scene.wro_pas_a_config.result_text = a

        return {'FINISHED'}


class WRO_PAS_A_panel(bpy.types.Panel):
    bl_label = "Parts Calculator"
    bl_idname = "wro_pas_a.main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Parts Calc'

    def draw(self, context):
        layout = self.layout
        # b = layout.box()
        layout.label(text='Object Name Prefixes')
        layout.textbox(
            bpy.context.scene.wro_pas_a_config,
            'topics',
            placeholder="Put here name prefixes of objects"
        )

        layout.separator()

        layout.prop(
            bpy.context.scene.wro_pas_a_config,
            'among_selected'
        )

        layout.separator()

        layout.prop(
            bpy.context.scene.wro_pas_a_config,
            'selected_object'
        )
        layout.prop(
            bpy.context.scene.wro_pas_a_config,
            'within_selected_object_imaginable_box'
        )
        layout.prop(
            bpy.context.scene.wro_pas_a_config,
            'allow_partial'
        )
        layout.operator(WRO_PAS_A_calc_all.bl_idname)

        layout.separator()

        layout.prop(
            bpy.context.scene.wro_pas_a_config,
            'result_text'
        )


class WRO_PAS_A_Config(bpy.types.PropertyGroup):

    topics: bpy.props.StringProperty(
        name="Topics",
        description="Topics to Search For"
    )

    among_selected: bpy.props.BoolProperty(
        name="Among Selected Only",
        description="Search Only Among Selected Objects",
        default=False
    )

    selected_object: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Box Object",
        description="Select object for below options"
    )

    within_selected_object_imaginable_box: bpy.props.BoolProperty(
        name="In Box",
        description="Search Only Withing Imaginable Box of Selected Object",
        default=False
    )

    allow_partial: bpy.props.BoolProperty(
        name="Accept Partial Objects",
        description="Include Objects Partially Located Within Imaginable Box",
        default=False
    )

    result_text: bpy.props.PointerProperty(
        type=bpy.types.Text,
        name="Result",
        description="Calculations Result Text Object"
    )


WRO_PAS_A_classes = [WRO_PAS_A_panel, WRO_PAS_A_calc_all, WRO_PAS_A_Config]


def register():
    for i in WRO_PAS_A_classes:
        bpy.utils.register_class(i)

    bpy.types.Scene.wro_pas_a_config = \
        bpy.props.PointerProperty(
            type=WRO_PAS_A_Config
        )


def unregister():

    del bpy.types.Scene.wro_pas_a_config

    for i in WRO_PAS_A_classes:
        bpy.utils.unregister_class(i)


def objects_list(inside_of=None):
    return bpy.data.objects


# def objects_list_in_selected_parallelepiped():
#    obj = bpy.context.active_object
#
#    obj_box = calc_obj_box(obj)


def calc_obj_box(obj):

    obj_coords = object_coords(obj)
    obj_coords = coords_list_matrix_convert(obj_coords, obj.matrix_world)

    min_x = get_minmax_xyz(obj_coords, 'min', 'x', 'value')
    min_y = get_minmax_xyz(obj_coords, 'min', 'y', 'value')
    min_z = get_minmax_xyz(obj_coords, 'min', 'z', 'value')
    max_x = get_minmax_xyz(obj_coords, 'max', 'x', 'value')
    max_y = get_minmax_xyz(obj_coords, 'max', 'y', 'value')
    max_z = get_minmax_xyz(obj_coords, 'max', 'z', 'value')

    ret = [min_x, min_y, min_z, max_x, max_y, max_z]
    if print_debug_messages:
        print("calc_obj_box(", obj, ") result:", ret)

    return ret


def couple_minmax(v1, v2):
    if (v1 > v2):
        return v2, v1
    else:
        return v1, v2


def calc_obj_box_minmaxes(obj_box):
    obj2_box_x_min, obj2_box_x_max = couple_minmax(obj_box[0], obj_box[3])
    obj2_box_y_min, obj2_box_y_max = couple_minmax(obj_box[1], obj_box[4])
    obj2_box_z_min, obj2_box_z_max = couple_minmax(obj_box[2], obj_box[5])

    return [obj2_box_x_min, obj2_box_x_max,
            obj2_box_y_min, obj2_box_y_max,
            obj2_box_z_min, obj2_box_z_max]


def obj_global_vertices(obj):
    ret = list(obj.data.vertices)
    for i in range(len(ret)):
        ret[i] = obj.matrix_world @ ret[i]
    return ret


def is_obj1_in_box_of_obj2(
        obj1,
        obj2,
        allow_partial=False,
        precalculated_box=None,
        precalculated_box_minmaxes=None,
        precalculated_obj1_global_coordinates=None
):
    is_in = 0

    if not precalculated_obj1_global_coordinates:
        precalculated_obj1_global_coordinates = coords_list_matrix_convert(
            object_coords(obj1),
            obj1.matrix_world
        )

    if precalculated_box:
        obj2_box = precalculated_box
    else:
        obj2_box = calc_obj_box(obj2)

    if precalculated_box_minmaxes:
        obj2_box_x_min, obj2_box_x_max, \
            obj2_box_y_min, obj2_box_y_max, \
            obj2_box_z_min, obj2_box_z_max = \
            precalculated_box_minmaxes
    else:
        obj2_box_x_min, obj2_box_x_max, \
            obj2_box_y_min, obj2_box_y_max, \
            obj2_box_z_min, obj2_box_z_max = \
            calc_obj_box_minmaxes(obj2_box)

    if print_debug_messages:
        print('obj2_box:', obj2_box)
        print('obj2_box_minmaxes:',
              obj2_box_x_min, obj2_box_x_max,
              obj2_box_y_min, obj2_box_y_max,
              obj2_box_z_min, obj2_box_z_max)

    for i in precalculated_obj1_global_coordinates:

        if (
            (i.x >= obj2_box_x_min and i.x < obj2_box_x_max) and
            (i.y >= obj2_box_y_min and i.y < obj2_box_y_max) and
            (i.z >= obj2_box_z_min and i.z < obj2_box_z_max)
        ):
            if print_debug_messages:
                print('vector', i, 'is in box of', obj2)
            is_in += 1

    if is_in == 0:
        if print_debug_messages:
            print("obj", obj1, ' not in ', obj2)
        return False

    if is_in == len(obj1.data.vertices):
        if print_debug_messages:
            print("obj", obj1, ' in ', obj2)
        return True

    if print_debug_messages:
        print("obj", obj1, ' partially in ', obj2)
    return allow_partial


def object_coords(obj):
    ret = list(obj.data.vertices)
    for i in range(len(ret)):
        ret[i] = ret[i].co
    return ret


def coords_list_matrix_convert(coord_list, matrix):
    ret = list()
    for i in coord_list:
        ret.append(matrix @ i)
    return ret


def get_minmax_xyz(coords, what, where, ret_type='value'):
    '''
    You pass object and this function searches
    it's points for min or max X, Y or Z and returns
    exact value or list of coordinates.

    coords must be list of mathutils.Vector

    throws exception in case of unrecovarable error.

    returns
       if nothing found (obj has no points):
       * None if 'value' requested for a result;
       * empty list, if 'vertex', 'vector' or 'same' is requested.
       else:
       * exact numeric value returned
       * list with all vertixes or vectors

    what: 'min' or 'max'
    where: 'x', 'y' or 'z'
    ret_type: 'value' or 'list'.
       if 'value' selected - exact value is returned.
       if 'list' selected - returned list of conforming bpy.types.MeshVertex es
    '''

    if what not in ['min', 'max']:
        raise Exception("invalid `what'")

    if where not in ['x', 'y', 'z']:
        raise Exception("invalid `where'")

    if ret_type not in ['value', 'list']:
        raise Exception("invalid `ret_type'")

    coords_type = type(coords)

    if print_debug_messages:
        print(
            "get_minmax_xyz(",
            coords, ", ",
            what,		", ",
            where, ", ", ret_type, ")"
        )

    if coords_type == list:
        for i in coords:
            coords_type_i = type(i)
            if coords_type_i != mathutils.Vector:
                raise Exception(
                    "unexpected value type in `coords' list: {}".format(
                        coords_type_i)
                )
    else:
        raise Exception("unsupported `obj' type: {}".format(coords_type))

    if len(coords) == 0:
        if ret_type == 'value':
            return None
        elif ret_type == 'list':
            return list()

    if print_debug_messages_get_minmax_xyz_in_coords:
        print("coords:")
        for i in range(len(coords)):
            print("   ", i, coords[i].xyz)

    val = getattr(coords[0], where)

    for i in coords[1:]:
        where_val = getattr(i, where)

        if ((what == 'min' and where_val < val) or
                (what == 'max' and where_val > val)):
            val = where_val

    if ret_type == 'value':
        return val
    elif ret_type == 'list':
        ret = []

        for i in coords:
            if getattr(i, where) == val:
                ret.append(i)
        return ret
    else:
        raise Exception("unexpected error")

    raise Exception("unexpected error")


def is_object_in_topic(topic, obj):
    return obj.name == topic or obj.name.startswith(topic+'.')


def get_objects(
    topics,
    among_selected=False,
    whithin_obj_box=None,
    allow_partial=False


):
    objs = []

    objs2 = []
    if among_selected:
        objs2 = list(bpy.context.selected_objects)
    else:
        objs2 = list(bpy.data.objects)

    precalculated_box = None
    precalculated_box_minmaxes = None
    if whithin_obj_box:
        precalculated_box = calc_obj_box(whithin_obj_box)
        precalculated_box_minmaxes = calc_obj_box_minmaxes(precalculated_box)

    for i in topics:
        for j in objs2:
            if is_object_in_topic(i, j):
                if (not whithin_obj_box or
                        is_obj1_in_box_of_obj2(
                            j,
                            whithin_obj_box,
                            allow_partial=allow_partial,
                            precalculated_box=precalculated_box,
                            precalculated_box_minmaxes=precalculated_box_minmaxes
                            # precalculated_obj1_global_coordinates not needed here
                        )):
                    objs.append(j)

    return objs


def calc_vertex_distance(v1, v2):
    for i in [v1, v2]:
        if type(i) != mathutils.Vector:
            raise Exception("parameters must be of type mathutils.Vector")

    x1 = decimal.Decimal(v1.x)
    x2 = decimal.Decimal(v2.x)
    y1 = decimal.Decimal(v1.y)
    y2 = decimal.Decimal(v2.y)
    z1 = decimal.Decimal(v1.z)
    z2 = decimal.Decimal(v2.z)

    if x1 > x2:
        t = x1
        x1 = x2
        x2 = t

    if y1 > y2:
        t = y1
        y1 = y2
        y2 = t

    if z1 > z2:
        t = z1
        z1 = z2
        z2 = t

    x_diff = x2-x1
    y_diff = y2-y1
    z_diff = z2-z1

    diff = ((x_diff ** 2) +
            (y_diff ** 2) +
            (z_diff ** 2)
            ).sqrt()

    diff = round(diff, 3)

    return diff


def calc_obj_length(obj):

    obj_coords = object_coords(obj)
    obj_coords = coords_list_matrix_convert(obj_coords, obj.matrix_world)

    longest = decimal.Decimal(0)

    for ed in obj.data.edges:
        dist = calc_vertex_distance(
            obj_coords[ed.vertices[0]],
            obj_coords[ed.vertices[1]]
        )
        if dist > longest:
            longest = dist
    return longest


def calc_pices(objs, topics):
    ret = {}

    for topic in topics:
        total_length = decimal.Decimal(0)
        lengths_reg = {}

        for obj in objs:
            if is_object_in_topic(topic, obj):

                obj_length = calc_obj_length(obj)

                total_length += obj_length

                if obj_length not in lengths_reg:
                    lengths_reg[obj_length] = decimal.Decimal(0)

                lengths_reg[obj_length] += decimal.Decimal(1)

        ret[topic] = {
            'total_length': total_length,
            'lengths_reg': lengths_reg
        }

    return ret


def calc_pices_res_repr(data):

    if print_debug_messages:
        print('data:', data)

    ret = ""

    keys = list(data.keys())

    keys.sort()

    for i in keys:
        ret += "{}:\n".format(i)

        ret += "\ttotal length: {}\n".format(data[i]['total_length'])
        reg = data[i]['lengths_reg']
        sizes = list(reg.keys())
        sizes.sort()
        for s in sizes:
            ret += "\t\tsize {}: count {}\n".format(s, reg[s])

    return ret
