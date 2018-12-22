# filler.py

"""
Given a properly-formatted csv file, post rubric entries to Canvas gradebook.
"""

import argparse
import canvasapi
import csv
import json
import os
import requests
import sys
import time

SID = "SID"
HTTP_SUCCESS = 200
VERBOSE = False


class GradePoster(object):

    def __init__(self, canvas_url, canvas_key, course_id, assignment_id,
                 csv_path):
        self.canvas_url = canvas_url
        self.canvas_key = canvas_key
        self.course_id = course_id
        self.assignment_id = assignment_id
        self.csv = csv_path
        self.successes = {}
        self.failures = {}

        criteria = self.get_rubric_info(self.course_id, self.assignment_id)
        expected = self.csv_expected_format(criteria)

        if self.csv is None:
            print("given that the assignment with id: {} has a rubric with \
criteria: {}\nthe csv is expected to have exactly the {} following columns (\
and header):\n{}".format(self.assignment_id, criteria, len(expected),
                         ",".join(expected)))
            sys.exit(0)

        csvfile = open(self.csv, encoding='utf-8-sig', newline='')
        self.dict_reader = csv.DictReader(csvfile)
        fields = self.dict_reader.fieldnames
        if not set(expected) == set(fields):
            message = "invalid csv headers. expected: {}, but got: {}".format(
                expected, actual)
            print(message)
            sys.exit(0)

    def get_rubric_info(self, course_id, assignment_id):
        canvas = canvasapi.Canvas(self.canvas_url, self.canvas_key)
        course = canvas.get_course(course_id)
        assignment = course.get_assignment(assignment_id)
        criteria_id = [[criterion["description"], criterion["points"],
                        criterion["id"]] for criterion in assignment.rubric]
        return criteria_id

    def csv_expected_format(self, criteria_id):
        return [SID]+[elem[2] for elem in criteria_id]

    def status_message(self):
        plural_success = {False: "", True: "es"}
        plural_failure = {False: "", True: "s"}
        success_count = len(self.successes.keys())
        failure_count = len(self.failures.keys())
        return "{} success{} and {} failure{}".format(
            str(success_count).rjust(6),
            plural_success[success_count != 1],
            str(failure_count).rjust(6),
            plural_failure[failure_count != 1])

    def post_all(self):
        for row in self.dict_reader:
            sid = row[SID]
            crit_grade_comments = {}
            for item in filter(lambda x: x != SID, row):
                crit_grade_comments[item] = {"points": row[item]}
            response = self.post_grade_update(sid, crit_grade_comments)
            if response.ok:
                if VERBOSE:
                    print(response)
                self.successes[sid] = crit_grade_comments
            else:  # failure case
                crit_grade_comments["error_message"] = response
                self.failures[sid] = crit_grade_comments
            sys.stdout.write('\r'+str(self.status_message()).ljust(60))
            sys.stdout.flush()
        sys.stdout.write('\r')
        sys.stdout.flush()

        success_count = len(self.successes.keys())
        suffix = "es"
        if success_count > 0:
            if success_count == 1:
                suffix = ""
            print(success_count, "success" + suffix)

        failure_count = len(self.failures.keys())
        suffix = "s"
        if failure_count > 0:
            if failure_count == 1:
                suffix = ""
            print(failure_count, " failure" + suffix, ": ", self.failures)

    def post_grade_update(self, student_id, crit_grade_comments):
        url_string = ("{}api/v1/courses/{}"
                      "/assignments/{}/submissions")
        url = url_string.format(self.canvas_url, self.course_id,
                                self.assignment_id)
        form_data = {"rubric_assessment": {}}
        url += "/{}"
        url = url.format(student_id)
        for crit in crit_grade_comments:
            form_data['rubric_assessment'][crit] = {
                "points": crit_grade_comments[crit]["points"]
            }
            if "comment" in crit_grade_comments[crit] and \
                    len(crit_grade_comments[crit]["comment"]) > 0:
                form_data['rubric_assessment'][crit]["comments"] = \
                    crit_grade_comments[crit]["comment"]
        data = str.encode(json.dumps(form_data))
        header = {"Authorization": "Bearer {}".format(self.canvas_key)}
        return requests.put(url, data, headers=header)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--canvas_key",
        default=None,
        help="your canvas account token. see: https://canvas.instructure.com/doc/api/file.oauth.html#manual-token-generation")

    parser.add_argument(
        "--canvas_url",
        default=None,
        help="the URL of your canvas instance, e.g. https://canvas.jmu.edu/")

    parser.add_argument("course", help="canvas course id")
    parser.add_argument("assignment", help="canvas assignment id")
    parser.add_argument(
        "csv", help="csv file with header: SID, crit1_id, crit2_id...",
        nargs="?", default=None)
    parser.add_argument("--verbose", help="increase output verbosity",
                        action="store_true")
    args = parser.parse_args()
    canvas_key = None
    canvas_url = None
    canvas_info_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "canvas_info.txt")

    canvas_key = args.canvas_key
    canvas_url = args.canvas_url
    
    if canvas_key is None or canvas_url is None:
        file_canvas_key = None
        file_canvas_url = None
        if os.path.isfile(canvas_info_path):
            with open(canvas_info_path) as f:
                try: 
                    file_canvas_key = next(f).strip()
                    file_canvas_url = next(f).strip()
                except Exception as e:
                    print("expected the file to be better, sad face.")
            if args.canvas_key is None:
                # get the constants file
                if file_canvas_key is not None:
                    canvas_key = file_canvas_key
            if args.canvas_url is None:
                # get the constants file
                if file_canvas_url is not None:
                    canvas_url = file_canvas_url
        if canvas_key is None:
            canvas_key = os.getenv("CANVAS_KEY")
        if canvas_url is None:
            canvas_url = os.getenv("CANVAS_URL")

    if canvas_key is None:
        print("Could not determine your CANVAS_KEY. Looked for (1) \
commandline argument --canvas_key, (2) 1st line in {}, \
(3) environment variable named CANVAS_KEY".format(canvas_info_path))
        sys.exit(1)

    if canvas_url is None:
        print("Could not determine your CANVAS_URL. Looked for (1) \
commandline argument --canvas_url, (2) 2nd line in {}, \
(3) environment variable named CANVAS_URL".format(canvas_info_path))
        sys.exit(1)

    course_id = int(args.course)
    assignment_id = int(args.assignment)
    VERBOSE = args.verbose

    gp = GradePoster(
        canvas_url,
        canvas_key,
        course_id,
        assignment_id,
        args.csv)
    gp.post_all()

if __name__ == "__main__":
    main()
