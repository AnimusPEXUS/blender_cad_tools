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


class WRO_PAS_A_calc_all(bpy.types.Operator):
    bl_idname = "wro_pas_a.calc_all"
    bl_label = "Perform Search"
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


def objects_list_in_selected_parallelepiped():
    obj = bpy.context.active_object

    obj_box = calc_obj_box(obj)


def calc_obj_box(obj):
    min_x = get_minmax_xyz(obj, 'min', 'x', 'value')
    min_y = get_minmax_xyz(obj, 'min', 'y', 'value')
    min_z = get_minmax_xyz(obj, 'min', 'z', 'value')
    max_x = get_minmax_xyz(obj, 'max', 'x', 'value')
    max_y = get_minmax_xyz(obj, 'max', 'y', 'value')
    max_z = get_minmax_xyz(obj, 'max', 'z', 'value')

    return [min_x, min_y, min_z, max_x, max_y, max_z]


def is_obj1_in_box_of_obj2(
        obj1,
        obj2,
        allow_partial=False,
        precalculated_box=None
):
    if precalculated_box:
        obj2_box = precalculated_box
    else:
        obj2_box = calc_obj_box(obj2)

    is_in = 0

    for i in obj1.data.vertices:
        i_co = i.co

        if (
            (i_co.x >= obj2_box[0] and i_co.x < obj2_box[3]) and
            (i_co.y >= obj2_box[1] and i_co.y < obj2_box[4]) and
            (i_co.z >= obj2_box[2] and i_co.z < obj2_box[5])
        ):
            is_in += 1

    if is_in == 0:
        return False

    if is_in == len(obj1.data.vertices):
        return True

    return allow_partial


def get_minmax_xyz(obj, what, where, ret_type='value'):
    '''
    You pass object and this function searches
    it's points for min or max X, Y or Z and returns
    exact value or list of vertexes.

    obj can be:
      *. bpy.types.Object
      *. a list of bpy.types.MeshVertex

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

    t = type(obj)

    if t == bpy.types.Object:
        obj = list(obj.data.vertices)

    elif t == list:
        for i in obj:
            t = type(i)
            if t != bpy.types.MeshVertex:
                raise Exception(
                    "unexpected value type in `obj' list: {}".format(t)
                )
    else:
        raise Exception("unsupported `obj' type: {}".format(t))

    if len(obj) == 0:
        if ret_type == 'value':
            return None
        elif ret_type == 'list':
            return list()

    val = getattr(obj[0].co, where)

    for i in obj[1:]:
        x = getattr(i.co, where)
        if (what == 'min' and x < val) or (what == 'max' and x > val):
            val = x

    if ret_type == 'value':
        return val
    elif ret_type == 'list':
        ret = []
        for i in obj:
            if getattr(i.co, where) == val:
                ret.append(i)
        return ret
    else:
        Exception("unexpected error")

    return None


def is_object_in_topic(topic, obj):
    return obj.name == topic or obj.name.startswith(topic+'.')


def get_objects(
    names,
    among_selected=False,
    whithin_obj_box=None,
    allow_partial=False
):
    objs = []

    objs2 = []
    if not among_selected:
        objs2 = bpy.data.objects
    else:
        objs2 = bpy.context.selected_objects

    precalculated_box = None
    if whithin_obj_box:
        precalculated_box = calc_obj_box(whithin_obj_box)

    for i in names:
        # i_dot = i+'.'
        for j in objs2:
            if is_object_in_topic(i, j):
                if (
                    whithin_obj_box is None or
                    is_obj1_in_box_of_obj2(
                        j,
                        whithin_obj_box,
                        allow_partial=allow_partial,
                        precalculated_box=precalculated_box
                    )
                ):
                    objs.append(j)

    return objs


def calc_vertex_distance(v1, v2):
    for i in [v1, v2]:
        if type(i) != bpy.types.MeshVertex:
            raise Exception("parameters must be of type bpy.types.MeshVertex")

    x1 = decimal.Decimal(v1.co.x)
    x2 = decimal.Decimal(v2.co.x)
    y1 = decimal.Decimal(v1.co.y)
    y2 = decimal.Decimal(v2.co.y)
    z1 = decimal.Decimal(v1.co.z)
    z2 = decimal.Decimal(v2.co.z)

    if x1 > x2:
        z = x1
        x1 = x2
        x2 = z

    if y1 > y2:
        z = y1
        y1 = y2
        y2 = z

    if z1 > z2:
        z = z1
        z1 = z2
        z2 = z

    x_diff = x2-x1
    y_diff = y2-y1
    z_diff = z2-z1

    diff = ((x_diff ** 2) +
            (y_diff ** 2) +
            (z_diff ** 2)
            ).sqrt()

    diff = round(diff, 3)

    return diff


def calc_pices(objs, topics):
    ret = {}

    for topic in topics:
        total_length = decimal.Decimal(0)
        lengths_reg = {}
        for obj in objs:
            if is_object_in_topic(topic, obj):
                longest = decimal.Decimal(0)
                for ed in obj.data.edges:
                    dist = calc_vertex_distance(
                        obj.data.vertices[ed.vertices[0]],
                        obj.data.vertices[ed.vertices[1]]
                    )
                    if dist > longest:
                        longest = dist

                total_length += longest
                if longest not in lengths_reg:
                    lengths_reg[longest] = decimal.Decimal(0)
                lengths_reg[longest] += decimal.Decimal(1)

        ret[topic] = {
            'total_length': total_length,
            'lengths_reg': lengths_reg
        }

    return ret


def calc_pices_res_repr(data):

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
