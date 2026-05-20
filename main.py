import pickle
from collections import UserDict
from datetime import datetime, date, timedelta

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:  # validation duplicated in validate_contact
            raise ValueError(f"Phone number must contain exactly 10 digits: {value}")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()  # format DD.MM.YYYY
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        phone_tmp = self.find_phone(phone)  # phone search
        if phone_tmp:
            self.phones.remove(phone_tmp)  # remove if phone exists
        else:
            raise ValueError(f"There is no such phone to remove: {phone_tmp}")

    def edit_phone(self, old_phone, new_phone):
        phone_tmp = self.find_phone(old_phone)  # searching the phone
        if not phone_tmp:
            raise ValueError(f"Phone {old_phone} not found")
        action = self.phones.index(phone_tmp)
        self.phones[action] = Phone(new_phone)

    def find_phone(self, phone):
        return next((p for p in self.phones if p.value == phone), None)

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        birthday = str(self.birthday) if self.birthday else "N/A"
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {birthday}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):  # adopted from previous homework
        today = date.today()
        upcoming_birthdays = []

        for record in self.data.values():
            if not record.birthday:
                continue

            upcoming_this_year = record.birthday.value.replace(year=today.year)  # changing year to current to compare only days

            if upcoming_this_year < today:  # moving past birthdays to next year
                upcoming_this_year = upcoming_this_year.replace(year=today.year + 1)

            days_until = (upcoming_this_year - today).days  # main calculation

            if 0 <= days_until <= 7:  # weekends checks
                if upcoming_this_year.weekday() == 5:
                    congratulation_date = upcoming_this_year + timedelta(days=2)
                elif upcoming_this_year.weekday() == 6:
                    congratulation_date = upcoming_this_year + timedelta(days=1)
                else:
                    congratulation_date = upcoming_this_year

                upcoming_birthdays.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y"),
                })

        return upcoming_birthdays


def save_data(book, filename="addressbook.pkl"):  # saving data to file
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):  # loading data from file
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


# bot

def input_error(func):  # decorator for errors processing
    def inner(*args, **kwargs):  # works for various inputs
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e) or "Enter the argument for the command"
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter user name."
    return inner


def show_help():    #help function
    return (
        "Available commands:\n"
        "  hello                          - greet the bot\n"
        "  add <name> <phone>             - add or update a contact\n"
        "  change <name> <old> <new>      - change phone number\n"
        "  phone <name>                   - show phone number\n"
        "  all                            - show all contacts\n"
        "  add-birthday <name> <DD.MM.YYYY> - add birthday\n"
        "  show-birthday <name>           - show birthday\n"
        "  birthdays                      - upcoming birthdays (next 7 days)\n"
        "  help                           - show this message\n"
        "  close / exit                   - quit the bot"
    )


def parse_input(user_input):    #input parsing
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


def validate_contact(name, phone):  #validation of adding Name and phone
    if not name.isalpha():
        return "Error: name must contain only letters."
    if not phone.isdigit() or len(phone) != 10:
        return "Error: phone must contain exactly 10 digits."
    return None


@input_error
def add_contact(args, book: AddressBook):    #adding contact to address book
    name, phone = args  # ValueError if args count != 2
    error = validate_contact(name, phone)
    if error:
        return error
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook): #changing existing contact
    name, old_phone, new_phone = args  # ValueError if args count != 3
    record = book.find(name)
    if not record:
        raise KeyError(name)
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook): #showing existing contact phones
    name = args[0]      # IndexError if no name provided
    record = book.find(name)
    if not record:
        raise KeyError(name)
    return "; ".join(p.value for p in record.phones)


@input_error
def show_all(book: AddressBook): #show all contacts
    if not book.data:
        return "No contacts saved."
    return "\n".join(str(r) for r in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    name, bday = args  # ValueError if args count != 2
    record = book.find(name)
    if not record:
        raise KeyError(name)
    record.add_birthday(bday)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]      # IndexError if no name provided
    record = book.find(name)
    if not record:
        raise KeyError(name)
    if not record.birthday:
        return f"{name} has no birthday set."
    return str(record.birthday)


@input_error
def birthdays(book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    return "\n".join(f"{e['name']}: {e['congratulation_date']}" for e in upcoming)


book = load_data()  # getting data from file on load
print("Welcome to the assistant bot! For commands list type help")

while True:
    user_input = input("Enter a command: ").strip()
    if not user_input:
        continue

    command, *args = parse_input(user_input)

    match command:
        case "close" | "exit":
            save_data(book)  # saving data to file on exit
            print("Good bye!")
            break
        case "help":
            print(show_help())
        case "hello":
            print("How can I help you?")
        case "add":
            print(add_contact(args, book))
        case "change":
            print(change_contact(args, book))
        case "phone":
            print(show_phone(args, book))
        case "all":
            print(show_all(book))
        case "add-birthday":
            print(add_birthday(args, book))
        case "show-birthday":
            print(show_birthday(args, book))
        case "birthdays":
            print(birthdays(book))
        case _:
            print("Invalid command. Type help for command list")
