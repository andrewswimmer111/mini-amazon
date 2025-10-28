from sqlalchemy import create_engine, text

from sqlalchemy import text

class DB:
    def __init__(self, app):
        self.engine = create_engine(
            app.config['SQLALCHEMY_DATABASE_URI'],
            execution_options={"isolation_level": "SERIALIZABLE"}
        )

    def execute(self, sqlstr, params=None, **kwargs):
        """
        Execute a single SQL statement.
        Accepts either:
          - params: a tuple/list (positional parameters) or a dict (named params)
          - OR keyword args (named params)

        Examples callers supported:
          db.execute(sql)                          # no params
          db.execute(sql, (seller_id,))           # positional
          db.execute(sql, {'seller_id': id})      # dict
          db.execute(sql, seller_id=id)           # kwargs
        """
        stmt = text(sqlstr)

        with self.engine.begin() as conn:
            # Prefer explicit params argument first
            if params is not None:
                # params might be a dict or a tuple/list
                result = conn.execute(stmt, params)
            elif kwargs:
                # named params passed as keywords
                result = conn.execute(stmt, kwargs)
            else:
                # no params
                result = conn.execute(stmt)

            if result.returns_rows:
                return result.fetchall()
            else:
                return result.rowcount
