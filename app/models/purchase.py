from flask import current_app as app


class Purchase:
    def __init__(self, purchase_id, buyer_id, date, address, fulfillment_status):
        self.purchase_id = purchase_id
        self.buyer_id = buyer_id
        self.date = date
        self.address = address
        self.fulfillment_status = fulfillment_status


    @staticmethod
    def get(id):
        rows = app.db.execute('''
SELECT id, uid, pid, time_purchased
FROM Purchases
WHERE id = :id
''',
                              id=id)
        return Purchase(*(rows[0])) if rows else None

    @staticmethod
    def get_all_by_uid_since(uid, since):
        rows = app.db.execute('''
SELECT purchase_id, buyer_id, date, address, fulfillment_status
FROM Purchases
WHERE buyer_id = :uid
AND date >= :since
ORDER BY date DESC
''', uid=uid, since=since)

        return [Purchase(*row) for row in rows]
