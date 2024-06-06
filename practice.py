import redis


class Museum:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.StrictRedis(host=host, port=port,
                                       db=db, decode_responses=True)
        self.current_admin = None

    def _get_admins_key(self):
        return 'museum:admins'

    def _get_exhibit_key(self, exhibit_id):
        return f'museum:exhibits:{exhibit_id}'

    def _get_exhibit_people_key(self, exhibit_id):
        return self._get_exhibit_key(exhibit_id) + ':related_people'

    def _get_person_key(self, person_id):
        return f'museum:people:{person_id}'

    def _get_person_exhibits_key(self, person_id):
        return self._get_person_key(person_id) + ':related_exhibits'

    def _check_login(self):
        if self.current_admin is None:
            print('Ви не ввійшли як адміністратор')
            return False
        return True

    def add_admin(self, admin_id, password):
        admins_key = self._get_admins_key()

        if self.redis.hexists(admins_key, admin_id):
            print('Адміністратор вже існує')
            return

        self.redis.hset(admins_key, admin_id, password)
        print('Адміністратора додано')

    def login(self, admin_id, password):
        admins_key = self._get_admins_key()

        admin_password = self.redis.hget(admins_key, admin_id)

        if admin_password is not None and password == admin_password:
            print('Вхід дозволено')
            self.current_admin = admin_id
        else:
            print('Невірний логін або пароль')

    def add_exhibit(self, exhibit_id, exhibit_data):
        if not self._check_login():
            return

        exhibit_key = self._get_exhibit_key(exhibit_id)

        if self.redis.exists(exhibit_key):
            print('Експонат вже є в базі даних музею')
            return

        data = {
            'admin': self.current_admin,
            'name': exhibit_data.get('name', ''),
            'description': exhibit_data.get('description', ''),
            'type': exhibit_data.get('type', ''),
        }

        self.redis.hset(exhibit_key, mapping=data)

        exhibit_people_key = self._get_exhibit_people_key(exhibit_id)

        people = exhibit_data.get('people', [])
        self.redis.sadd(exhibit_people_key, *people)

        for person_id in people:
            person_exhibits_key = self._get_person_exhibits_key(person_id)
            self.redis.sadd(person_exhibits_key, exhibit_id)

        print('Експонат додано')

    def delete_exhibit(self, exhibit_id):
        if not self._check_login():
            return

        exhibit_key = self._get_exhibit_key(exhibit_id)

        if not self.redis.exists(exhibit_key):
            print('Немає експоната в базі даних музею')
            return

        # видалення даних про експонат
        self.redis.delete(exhibit_key)

        # пов'язані люди
        exhibit_people_key = self._get_exhibit_people_key(exhibit_id)
        people = self.redis.smembers(exhibit_people_key)
        self.redis.delete(exhibit_people_key)

        # видалення експонату з даних людей
        for person_id in people:
            person_exhibits_key = self._get_person_exhibits_key(person_id)
            self.redis.srem(person_exhibits_key, exhibit_id)

        print('Дані про експонат видалено')

    def edit_exhibit(self, exhibit_id, exhibit_data):
        if not self._check_login():
            return

        exhibit_key = self._get_exhibit_key(exhibit_id)

        if not self.redis.exists(exhibit_key):
            print('Немає експоната в базі даних музею')
            return

        current_data = self.redis.hgetall(exhibit_key)
        updated_data = {
            'admin': self.current_admin,
            'name': exhibit_data.get('name', current_data.get('name', '')),
            'description': exhibit_data.get('description', current_data.get('description', '')),
            'type': exhibit_data.get('type', current_data.get('type', '')),
        }

        self.redis.hset(exhibit_key, mapping=updated_data)

        current_people = self.redis.smembers(self._get_exhibit_people_key(exhibit_id))
        new_people = set(exhibit_data.get('people', []))

        added_people = new_people - current_people
        removed_people = current_people - new_people

        exhibit_people_key = self._get_exhibit_people_key(exhibit_id)
        self.redis.sadd(exhibit_people_key, *added_people)
        self.redis.srem(exhibit_people_key, *removed_people)

        for person_id in added_people:
            person_exhibits_key = self._get_person_exhibits_key(person_id)
            self.redis.sadd(person_exhibits_key, exhibit_id)

        for person_id in removed_people:
            person_exhibits_key = self._get_person_exhibits_key(person_id)
            self.redis.srem(person_exhibits_key, exhibit_id)

        print('Дані про експонат оновлено')

    def view_exhibit_info(self, exhibit_id):
        if not self._check_login():
            return

        exhibit_key = self._get_exhibit_key(exhibit_id)

        if not self.redis.exists(exhibit_key):
            print('Немає експоната в базі даних музею')
            return

        exhibit_data = self.redis.hgetall(exhibit_key)

        print(f'\t\t Назва: {exhibit_data.get("name", "Невідомо")}')
        print(f'\t\t Опис: {exhibit_data.get("description", "Невідомо")}')
        print(f'\t\t Адміністратор, що вніс дані: {exhibit_data.get("admin", "Невідомо")}')

        exhibit_people_key = self._get_exhibit_people_key(exhibit_id)

        people = self.redis.smembers(exhibit_people_key)

        if people:
            print('\t\t\t Пов\'язані особистості: ', *people)

    def view_all_exhibits(self):
        pattern_key = self._get_exhibit_key('*')
        exhibits_keys = self.redis.keys(pattern=pattern_key)

        for key in exhibits_keys:
            exhibit_id = key.split(':')[-1]

            if exhibit_id.isdigit():
                print(f'Дані про експонат з ID {exhibit_id}')
                self.view_exhibit_info(exhibit_id)

                print()

    def view_people_related_to_exhibit(self, exhibit_id):
        exhibit_people_key = self._get_exhibit_people_key(exhibit_id)
        people = self.redis.smembers(exhibit_people_key)

        if not people:
            print(f'Немає пов\'язаних осіб для експоната з ID {exhibit_id}')
        else:
            print(f'Особи, пов\'язані з експонатом {exhibit_id}: {", ".join(people)}')

    def view_exhibits_related_to_person(self, person_id):
        person_exhibits_key = self._get_person_exhibits_key(person_id)
        exhibits = self.redis.smembers(person_exhibits_key)

        if not exhibits:
            print(f'Немає пов\'язаних експонатів для особи з ID {person_id}')
        else:
            print(f'Експонати, пов\'язані з особою {person_id}: {", ".join(exhibits)}')

    def view_exhibits_by_type(self, exhibit_type):
        pattern_key = self._get_exhibit_key('*')
        exhibits_keys = self.redis.keys(pattern=pattern_key)

        for key in exhibits_keys:
            exhibit_data = self.redis.hgetall(key)
            if exhibit_data.get('type') == exhibit_type:
                exhibit_id = key.split(':')[-1]
                print(f'Дані про експонат з ID {exhibit_id}')
                self.view_exhibit_info(exhibit_id)
                print()


museum = Museum()

while True:
    print('Оберіть функцію')
    print('1. Реєстрація адміністратору музею')
    print('2. Вхід')
    print('3. Додати експонат')
    print('4. Видалити експонат')
    print('5. Редагувати інформацію про експонат')
    print('6. Вивести інформацію про експонат')
    print('7. Вивести інформацію про всі експонати')
    print('8. Вивести інформацію про людей, які мають відношення до експоната')
    print('9. Вивести інформацію про експонати, що мають відношення до певної особи')
    print('10. Вивести експонати за типом')

    command = int(input('Введіть номер команди: '))

    if command == 1:
        admin_id = int(input('Введіть id адміністратора: '))
        password = input('Введіть пароль: ')

        museum.add_admin(admin_id, password)
        print('=====================================')
        print('=====================================')

    elif command == 2:
        admin_id = int(input('Введіть id адміністратора: '))
        password = input('Введіть пароль: ')

        museum.login(admin_id, password)
        print('=====================================')
        print('=====================================')

    elif command == 3:
        exhibit_id = int(input('Введіть id експоната: '))

        exhibit_data = {
            'name': input('введіть ім\'я експоната: '),
            'description': input('введіть опис експоната: '),
            'type': input('введіть тип експоната: '),
            'people': input('введіть пов\'язаних з експонатом людей: ').split(',')
        }

        museum.add_exhibit(exhibit_id, exhibit_data)
        print('=====================================')
        print('=====================================')

    elif command == 4:
        exhibit_id = int(input('Введіть id експоната: '))

        museum.delete_exhibit(exhibit_id)
        print('=====================================')
        print('=====================================')

    elif command == 5:
        exhibit_id = int(input('Введіть id експоната: '))

        exhibit_data = {
            'name': input('введіть ім\'я експоната (або залиште порожнім для збереження поточного): '),
            'description': input('введіть опис експоната (або залиште порожнім для збереження поточного): '),
            'type': input('введіть тип експоната (або залиште порожнім для збереження поточного): '),
            'people': input('введіть пов\'язаних з експонатом людей (через кому): ').split(',')
        }

        museum.edit_exhibit(exhibit_id, exhibit_data)
        print('=====================================')
        print('=====================================')

    elif command == 6:
        exhibit_id = int(input('Введіть id експоната: '))

        museum.view_exhibit_info(exhibit_id)
        print('=====================================')
        print('=====================================')

    elif command == 7:
        museum.view_all_exhibits()
        print('=====================================')
        print('=====================================')

    elif command == 8:
        exhibit_id = int(input('Введіть id експоната: '))
        museum.view_people_related_to_exhibit(exhibit_id)
        print('=====================================')
        print('=====================================')

    elif command == 9:
        person_id = int(input('Введіть id особи: '))
        museum.view_exhibits_related_to_person(person_id)
        print('=====================================')
        print('=====================================')

    elif command == 10:
        exhibit_type = input('Введіть тип експоната: ')
        museum.view_exhibits_by_type(exhibit_type)
        print('=====================================')
        print('=====================================')
