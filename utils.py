import bpy


def find_layer_collection(layer_collection, collection_name, parent_name=None):
    found = layer_collection.children.get(collection_name)
    if found:
        # found it, does it have the right parent?
        if parent_name:
            if layer_collection.name == parent_name:
                return found
        else:
            return found
    else:
        # check all child layer collections for this collection
        for child in layer_collection.children.values():
            found = find_layer_collection(child, collection_name, parent_name)
            if found:
                return found
    return None


def set_active_layer_collection(view_layers, collection_name, parent_name=None):
    for view_layer in view_layers:
        found = find_layer_collection(view_layer.layer_collection, collection_name, parent_name)
        if found:
            view_layer.active_layer_collection = found
            return found
    return None


def set_active_collection(name='Photogrammetry', parent=None, **kwargs):
    scene = kwargs.get('scene', None)
    if scene:
        col = (parent or scene.collection).children.get(name)
        if not col:
            col = bpy.data.collections.new(name)
            (parent or scene.collection).children.link(col)
        set_active_layer_collection(scene.view_layers, col.name, parent.name if parent else None)
        return col
    return None
