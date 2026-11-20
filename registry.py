import sys
from collections import Counter
from people import Student, Teacher, AnketaError


class Registry:

    def __init__(self):
        self.accepted: list[Student | Teacher] = []
        self.rejected: list[tuple[int, str, str]] = []
        self.total_lines = 0

    def add(self, person: Student | Teacher):
        self.accepted.append(person)

    def add_rejected(self, line_num: int, raw_line: str, reason: str):
        self.rejected.append((line_num, raw_line, reason))

    def load(self, filename: str) -> bool:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"Ошибка: файл '{filename}' не найден!")
            return False

        self.total_lines = len(lines)

        for line_num, raw_line in enumerate(lines, start=1):
            cleaned = raw_line.strip()
            if not cleaned:
                continue

            parts = [p.strip() for p in raw_line.rstrip("\r\n").split(";")]

            if len(parts) != 5:
                self.add_rejected(line_num, cleaned, f"неверное количество полей: ожидалось 5, получено {len(parts)}")
                continue

            person_type, fio, email, phone, extra_field = parts

            try:
                if person_type == "s":
                    person = Student(fio, email, phone, extra_field)
                elif person_type == "t":
                    person = Teacher(fio, email, phone, extra_field)
                else:
                    raise AnketaError(f"неизвестный тип: {person_type}")

                self.add(person)
            except AnketaError as e:
                self.add_rejected(line_num, cleaned, str(e))

        self.accepted.sort()
        return True

    def __len__(self) -> int:
        return len(self.accepted)

    def print_report(self):
        w_num = 3
        w_fio = 28
        w_role = 15
        w_extra = 16
        w_phone = 18

        header = (
            f"{'№':<{w_num}} "
            f"{'ФИО':<{w_fio}} "
            f"{'Роль':<{w_role}} "
            f"{'Группа/кафедра':<{w_extra}} "
            f"{'Телефон':<{w_phone}}"
        )
        separator = "-" * len(header)

        print("=== ПРИНЯТЫЕ АНКЕТЫ ===")
        print(header)
        print(separator)
        for idx, person in enumerate(self.accepted, start=1):
            print(
                f"{idx:<{w_num}} "
                f"{person.fio:<{w_fio}} "
                f"{person.role():<{w_role}} "
                f"{person.extra():<{w_extra}} "
                f"{person.masked_phone():<{w_phone}}"
            )
        print(separator)

        print(f"\nОтклонено строк: {len(self.rejected)}")
        for line_num, raw_str, reason in self.rejected:
            print(f"  строка {line_num}: {reason}")
            print(f"     {raw_str}")

        print(f"\nПринято: {len(self.accepted)} | Отклонено: {len(self.rejected)}")

        role_counts = Counter(p.role() for p in self.accepted)
        print("\nПо ролям:")
        for role, count in role_counts.items():
            print(f"  {role:<15} {count}")

        extra_counts = Counter(p.extra() for p in self.accepted)
        print("\nПо группам/кафедрам:")
        for extra_val, count in extra_counts.items():
            print(f"  {extra_val:<15} {count}")

    def save_files(self, ok_filename: str, errors_filename: str):
        with open(ok_filename, "w", encoding="utf-8") as f_ok:
            f_ok.write(f"{'№':<3} | {'ФИО':<28} | {'Роль':<15} | {'Группа/кафедра':<16} | {'Телефон':<18}\n")
            f_ok.write("-" * 85 + "\n")
            for idx, person in enumerate(self.accepted, start=1):
                f_ok.write(
                    f"{idx:<3} | {person.fio:<28} | {person.role():<15} | "
                    f"{person.extra():<16} | {person.masked_phone():<18}\n"
                )

        with open(errors_filename, "w", encoding="utf-8") as f_err:
            for line_num, raw_str, reason in self.rejected:
                f_err.write(f"строка {line_num}: {reason}\n   {raw_str}\n")
