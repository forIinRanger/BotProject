from data.websites import Website


def change_ids(db_sess):
    counter = 1
    for i in db_sess.query(Website).all():
        i.id = counter
        counter += 1