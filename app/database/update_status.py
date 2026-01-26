# app/database/update_status.py

"""
Three steps to the process:

    1:
        a: scan database for all bookings with missing status.
            save the booking_id in a list
        b: upload all bookings from COMPLETED bookings since April 1 2019 and IF booking_id is in the list THEN
            copy booking_status into database record for booking_id AND
            delete booking_id from the list
    2:
        Upload all the CANCELLED bookings since April 1 2019 and  IF booking_id is in the list THEN
            copy booking_status into database record for booking_id AND
            delete booking_id from the list

    3: report all booking_ids still in the list (should be none)
"""

import json

from app import create_app, db
from flask import current_app
from app.models import Booking
import requests


class CompletedBookings(object):
    def __init__(self):
        self.base_url = "https://maid2match.launch27.com"
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "authorization": f"Bearer {self._get_api_key()}",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "referrer": f"{self.base_url}/admin/bookings",
            "referrerPolicy": "no-referrer-when-downgrade",
            "body": None,
            "method": "GET",
            "mode": "cors",
            "credentials": "include",
        }

    def _get_api_key(self):
        login_url = f"{self.base_url}/v1/login"
        referrer_url = f"{self.base_url}/login"
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json;charset=UTF-8",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "referrer": referrer_url,
            "referrerPolicy": "no-referrer-when-downgrade",
            "body": None,
            "method": "GET",
            "mode": "cors",
            "credentials": "include",
        }

        payload = {
            "email": current_app.config["L27_USERNAME"],
            "password": current_app.config["L27_PASSWORD"],
        }

        r = requests.post(login_url, headers=headers, data=json.dumps(payload))
        d = r.json()

        api_key = d["bearer"]

        return api_key

    def get_bookings(self, limit, offset, filter=None):
        url_base = f"{self.base_url}/v1/staff/bookings"
        if filter:
            params = {
                "filter": filter,
                "from": "2020-03-01",
                "limit": limit,
                "offset": offset,
                "options": "completed%2Cexclude_forecasted",
                "query": "",
                "sort": "asc",
                "to": "2020-10-12",
            }
        else:
            params = {
                "from": "2020-03-01",
                "limit": limit,
                "offset": offset,
                "options": "completed%2Cexclude_forecasted",
                "query": "",
                "sort": "asc",
                "to": "2020-10-12",
            }
        r = requests.get(url=url_base, headers=self.headers, params=params)

        if r.status_code != 200:
            raise ValueError(
                f"get_team_page:: Status_code: {r.status_code} text: {r.text}"
            )

        r_json = r.json()
        # print(f'get_completed_bookings[0]: {r_json[0]["id"]}')
        return r_json

    def get_booking_data(self, filter=None):
        limit = 100
        offset = 0
        items_read = 100

        while items_read == limit:
            r = self.get_bookings(limit, offset, filter)
            items_read = len(r)
            offset += limit
            for item in r:
                yield item


def completed_booking_ids(bids):
    completed = CompletedBookings()

    for b in completed.get_booking_data():
        if "id" in b:
            b_id = b["id"]
            if b_id in bids:
                if update_booking(b_id, "COMPLETED") == b_id:
                    print(f"completed match for {b_id}")

                    bids.remove(b_id)
    return bids


def cancelled_booking_ids(bids):
    completed = CompletedBookings()

    for b in completed.get_booking_data(filter="cancelled"):
        if "id" in b:
            b_id = b["id"]
            if b_id in bids:
                if update_booking(b_id, "CANCELLED") == b_id:
                    print(f"completed match for {b_id}")

                    bids.remove(b_id)
    return bids


def mark_incomplete_booking_ids(bids):
    for b_id in bids:
        if update_booking(b_id, "NOT_COMPLETE") == b_id:
            print(f"completed match for {b_id}")


def update_booking(b_id, status):
    res = db.session.query(Booking).filter(Booking.booking_id == b_id).first()

    if res is None:
        print(f"Whoops! lost booking {b_id} in Bookings")
        return None
    else:
        res.booking_status = status
        return b_id


def main():
    app = create_app()

    with app.app_context():
        res = db.session.query(Booking).filter(Booking.booking_status is None).all()

        print(f"booking ids to sort out = {len(res)}")

        if res:
            bids = set()
            for item in res:
                bids.add(item.booking_id)
            print(bids)

            bids_remaining = completed_booking_ids(bids)
            db.session.commit()

            print(f"booking ids to resolve = {len(bids_remaining)}")
            print(bids_remaining)

            bids_not_completed = cancelled_booking_ids(bids_remaining)
            db.session.commit()

            print(f"booking ids NOT_COMPLETED= {len(bids_not_completed)}")
            print(bids_not_completed)

            ### These remaining ones could be NOT_COMPLETE if _updated_at is greater than today
            mark_incomplete_booking_ids(bids_not_completed)
            db.session.commit()


if __name__ == "__main__":
    main()
