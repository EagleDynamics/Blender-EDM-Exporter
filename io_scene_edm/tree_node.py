
class TreeNode:
    def __init__(self) -> None:
        self.parent = None
        self.children = []

    def destroy(self):
        self.remove_children(self.children)
        self.parent = None

    def get_child_by_name(self, name):
        for c in self.children:
            if name == c.name:
                return c
        return None
    
    def add_child(self, o):
        assert o not in self.children

        self.children.append(o)
        o.parent = self
    
    def add_children(self, objects):
        for o in objects:
            self.add_child(o)
    
    def remove_child(self, o):
        assert o in self.children

        o.parent = None
        self.children.remove(o)

    def remove_children(self, objects):
        for o in objects:
            self.remove_child(o)
