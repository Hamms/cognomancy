
class Action:

    def __init__(self, action, value=None):
        self.action = action
        self.value = value

    def __str__(self):
        return "{}(())".format(self.action, self.value)

    def __repr__(self):
        return str(self)
