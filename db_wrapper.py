import sqlite3


class database:
    def __init__(self, file_database):
        self.db = file_database

    def read_(self, request_value):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        cur.execute(request_value)
        data = cur.fetchall()
        con.close()
        return data

    def entry_(self, request_value):
        cur = sqlite3.connect(self.db)
        cur.execute(request_value)
        cur.commit()
        cur.close()


class request_db(database):
    def request_select(self, output_fields, table, condition_field=None, condition=None):
        if condition_field:
            select_request = f'''
            SELECT {output_fields}
            FROM {table}
            WHERE {condition_field} = '{condition}'
            '''
        else:
            select_request = f'''
            SELECT {output_fields}
            FROM {table}
            '''
        return super().read_(select_request) 

    def request_select_join(self,
                            output_fields,
                            from_table,
                            join_table,
                            condition_field=None,
                            condition=None,
                            ):
        """
        :param output_fields: Поля вывода [таблица.поле]
        :param from_table: Таблица запроса
        :param join_table: Таблица подключения
        :param condition_field: Поле условия [таблица.поле]
        :param condition: Условие выборки
        """
        if condition:
            request_select = f'''
            SELECT {output_fields}
            FROM {from_table}
            INNER JOIN {join_table} on 
            {from_table}.login = {join_table}.user_id
            INNER JOIN Users on {join_table}.user_id = {from_table}.login
            WHERE {condition_field} = '{condition}'
            '''
        else:
            request_select = f'''
            SELECT {output_fields}
            FROM {from_table}
            INNER JOIN {join_table} on 
            {from_table}.login = {join_table}.user_id
            INNER JOIN Users on {join_table}.Users = {from_table}.id
            '''
        return super().read_(request_select)

    def request_insert(self, table, fields, *values):
        insert_request = f'''
        INSERT INTO {table} ({fields})
        VALUES ({values})
        '''
        super().entry_(insert_request)
        return super().read_(f'SELECT id FROM {table} ORDER BY id DESC LIMIT 1')

    def request_insert_one(self, table, field, value):
        insert_request = f'''
        INSERT INTO {table} ({field}) VALUES ('{value}')
        '''
        super().entry_(insert_request)
        return super().read_(f'SELECT id FROM {table} ORDER BY id DESC LIMIT 1')

    def request_insert_two(self, table, fields, value_1, value_2):
        insert_request = f'''
        INSERT INTO {table} ({fields})
         VALUES ('{value_1}', '{value_2}')
        '''
        super().entry_(insert_request)
        return super().read_(f'SELECT id FROM {table} ORDER BY id DESC LIMIT 1')

    def request_insert_three(self, table, fields, value_1, value_2, value_3):
        insert_request = f'''
        INSERT INTO {table} ({fields})
         VALUES ('{value_1}', '{value_2}', '{value_3}')
        '''
        super().entry_(insert_request)
        return super().read_(f'SELECT id FROM {table} ORDER BY id DESC LIMIT 1')

    def request_update(self, table, field_1, value_1, field_2, value_2):
        insert_request = f'''
        UPDATE {table}
        SET {field_1} = '{value_1}'
        WHERE {field_2} = '{value_2}'
        '''
        super().entry_(insert_request)

    def request_delete(self, table, condition_field, condition):
        request_delete = f'''
        DELETE FROM {table} WHERE {condition_field} = '{condition}'
        '''
        return super().entry_(request_delete)
