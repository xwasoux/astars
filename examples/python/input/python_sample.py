def wait_until_finished(self):
        """
        Waits until all processors are finished processing.

        The method iterates through the processors and waits for each one to finish.
        It uses a small sleep duration between checks to avoid unnecessary resource consumption.
        """
        for file_path, processor in self._processors.items():
            while not processor.done:
                time.sleep(0.1)
        
def rectangle_area(width: float, height: float) -> float:
    """
    Calculate the area of a rectangle.

    Args:
        width (float): The width of the rectangle.
        height (float): The height of the rectangle.

    Returns:
        float: The area of the rectangle.
    """
    return width * height

from dataclasses import dataclass
@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self) -> str:
        return f"Hello, my name is {self.name} and I am {self.age} years old."

    def get_bmi(self, weight_kg: float, height_m: float) -> float:
        return weight_kg / (height_m ** 2)

def main():
    # Example usage of the Person class
    person = Person(name="Alice", age=30)
    print(person.greet())
    bmi = person.get_bmi(weight_kg=70, height_m=1.75)
    print(f"My BMI is: {bmi:.2f}")

if __name__ == "__main__":
    main()
