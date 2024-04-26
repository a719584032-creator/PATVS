class SharedData:
    def __init__(self, initial_value=None):
        self.value = initial_value

# 分别在两个不同的类中使用这个共享数据
class ClassA:
    def __init__(self, shared_data):
        self.shared_data = shared_data

    def update_value(self, new_value):
        self.shared_data.value = new_value

class ClassB:
    def __init__(self, shared_data):
        self.shared_data = shared_data

    def print_value(self):
        print(self.shared_data.value)

# 创建一个共享数据对象
shared_data = SharedData(initial_value=0)

# 在两个类的实例间共享同一个数据
a = ClassA(shared_data)
b = ClassB(shared_data)

a.update_value(5)  # ClassA的实例更改了共享数据的值
b.print_value()    # ClassB的实例能够看到更新后的数据，输出 5