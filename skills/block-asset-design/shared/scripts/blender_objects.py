"""Explicit object selection shared by Blender tools."""

def choose_objects(bpy, names=None, collection=None):
    if names and collection: raise ValueError('choose object names OR a collection')
    if collection:
        col = bpy.data.collections.get(collection)
        if col is None: raise ValueError('collection not found: '+collection)
        objects = list(col.all_objects)
    elif names:
        missing = [n for n in names if n not in bpy.context.scene.objects]
        if missing: raise ValueError('objects missing: '+repr(missing))
        objects = [bpy.context.scene.objects[n] for n in names]
    else:
        objects = list(bpy.context.selected_objects)
    if not objects: raise ValueError('empty selection; select objects or specify names/collection')
    return objects
