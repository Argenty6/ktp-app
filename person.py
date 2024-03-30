class Person(object):
    def __init__(self, name: str, surname: str, age: int = None, nationality: str = ""):
        self.name = name
        self.surname = surname
        self.age = age
        self.nationality = nationality

    def set_age(self, age: int):
        self.age = age

    def __repr__(self) -> str:
        return f"Person with following information: Name: {self.name}, Surname: {self.surname} and Age: {self.age}"


class FrenchPerson(Person):
    def __init__(self, name: str, surname: str, age: int = None):
        super().__init__(name=name, surname=surname, age=age, nationality="french")


if __name__ == "__main__":
    a = Person(name="arnaud", surname="nansi", age=29)
    print(f"Name: {a.name}")
    print(f"Age: {a.age}")

    a.set_age(age=30)

    print(f"a: {a}")

    b = FrenchPerson(name="arnaud", surname="nansi", age=29)
    b.set_age(31)

    print(f"b: {b}")
