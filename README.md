# canvas-rubric-filler
Given a properly-formatted csv file, post rubric entries to Canvas gradebook.

## Usage

The Canvas-filler is designed to be as user-friendly as possible.
It needs several pieces of information to function:
1. `canvas_key`
    * if the script finds `CANVAS_KEY` in your environment, this argument is not expected.
1. `canvas_url`
    * if the script finds `CANVAS_URL` in your environment, this argument is not expected.
1. `course_id`
1. `assignment_id`
1. `student_rubric_values.csv`
    * if this is omitted, the script will print the expected headers for the csv file.

`python filler.py [canvas_key] [canvas_url] course_id assignment_id [student_rubric_values.csv]`

### Data

The headers of the csv should be:

**note: if you simply run the script without `student_rubric_values.csv`, it will print the expected headers automatically**

1. SID
2. ...The Rubric Criteria IDs 
    * these can come from the rubric page.  e.g. https://canvas.jmu.edu/courses/1584732/rubrics/687658
    inspect the table to get the criteria ids
    $(".criterion:not(.blank, #criterion_1)").map((i,e)=>e.id.substring("criterion_".length))

## Acknowledgements
1. Nathan Self @nwself and https://community.canvaslms.com/thread/15580-how-can-one-get-the-criterion-id-from-an-api-call
1. Nathan Sprague @sprgunr and https://github.com/JMU-CS/Upload-Canvas-Grades
1. https://github.com/ucfopen/canvasapi
