"""Item system — item definitions and player inventory."""


class Item:
    """Base item."""
    def __init__(self, item_id, name, item_type, description=''):
        self.id = item_id
        self.name = name
        self.type = item_type  # 'consumable', 'equipment', 'material'
        self.description = description
        self.stackable = (item_type in ('consumable', 'material'))
        self.count = 1

    def use(self, player):
        """Use the item on player. Override per item."""
        pass


class Inventory:
    """Simple inventory with limited slots."""
    def __init__(self, size=20):
        self.size = size
        self.items = []

    def add(self, item):
        """Add item to inventory. Returns True if successful."""
        if item.stackable:
            for existing in self.items:
                if existing.id == item.id:
                    existing.count += item.count
                    return True
        if len(self.items) < self.size:
            self.items.append(item)
            return True
        return False

    def remove(self, item_id, count=1):
        """Remove items by id. Returns True if successful."""
        for item in self.items:
            if item.id == item_id and item.count >= count:
                item.count -= count
                if item.count <= 0:
                    self.items.remove(item)
                return True
        return False

    def has(self, item_id):
        """Check if inventory contains item."""
        return any(i.id == item_id for i in self.items)
