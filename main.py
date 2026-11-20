import json
from registry import Registry
from people import Student, Teacher, AnketaError
from client import (
    poluchit_vse_ankety,
    proverka_pochty,
    poluchit_statistiku,
    ServerNedostupen,
)

INPUT_FILE = "anketa.txt"
OK_FILE = "ok.txt"
ERRORS_FILE = "errors.txt"
OTCHET_FILE = "otchet.json"


def zagruzit_s_servera(registry):

    try:
        ankety = poluchit_vse_ankety()
    except ServerNedostupen as e:
        print(f"Сервер недоступен: {e}")
        return False

    for a in ankety:
        nomer = a.get("nomer")
        tip = a.get("tip")
        fio = a.get("fio", "")
        mail = a.get("mail", "")
        phone = a.get("phone", "")

        try:
            if tip == "s":
                gruppa = a.get("gruppa", "")
                person = Student(fio, mail, phone, gruppa)
            elif tip == "t":
                kafedra = a.get("kafedra", "")
                person = Teacher(fio, mail, phone, kafedra)
            else:
                raise AnketaError(f"неизвестный тип: {tip}")
            registry.add(person)
        except AnketaError as e:
            registry.add_rejected(nomer, str(a), str(e))

    registry.accepted.sort()
    return True


def zagruzit_iz_fajla(registry, filename=INPUT_FILE):
    return registry.load(filename)


def main():
    registry = Registry()
    source = ""

    if zagruzit_s_servera(registry):
        source = "сервер"
    else:
        print("Переход на запасной источник — файл anketa.txt")
        if zagruzit_iz_fajla(registry):
            source = f"файл {INPUT_FILE}"
        else:
            print(f"Нет ни сервера, ни файла {INPUT_FILE}. Завершение.")
            return

    print(f"\nДанные взяты из: {source}\n")

    registry.print_report()

    server_stat = None
    try:
        server_stat = poluchit_statistiku()
        print("\n=== СТАТИСТИКА СЕРВЕРА ===")
        print(f"Всего анкет на сервере: {server_stat.get('vsego')}")
        print(f"По ролям на сервере: {server_stat.get('po_rolyam')}")
        print("\nПочему числа разные:")
        print("   Сервер просто считает все записи, не проверяя их.")
        print("   Наша программа применяет дополнительные проверки")
        print("   (формат почты, телефона и т.д.), поэтому некоторые")
        print("   анкеты отклоняются.")
    except ServerNedostupen:
        print("\nНе удалось получить статистику с сервера.")

    print("\n=== ПРОВЕРКА ПОЧТЫ ЧЕРЕЗ /proverka ===")
    for person in registry.accepted:
        result = proverka_pochty(person.email)
        print(f"  {person.fio}: {person.email} → {result}")

    report = {
        "source": source,
        "accepted_count": len(registry.accepted),
        "rejected_count": len(registry.rejected),
        "accepted": [],
        "rejected": [],
        "server_stat": server_stat,
    }

    for person in registry.accepted:
        report["accepted"].append({
            "fio": person.fio,
            "role": person.role(),
            "extra": person.extra(),
            "email": person.email,
            "phone": person.masked_phone(),
        })

    for line_num, raw, reason in registry.rejected:
        report["rejected"].append({
            "nomer": line_num,
            "raw": raw,
            "reason": reason,
        })

    with open(OTCHET_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nОтчёт сохранён в {OTCHET_FILE}")


if __name__ == "__main__":
    main()
