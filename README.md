# canvas-rubric-filler
Given a properly-formatted csv file, post rubric entries to Canvas gradebook.

The headers of the csv should be:
1. SID
2. ...The Rubric Criteria IDs 
    * these can come from the rubric page.  e.g. https://canvas.jmu.edu/courses/1584732/rubrics/687658
    inspect the table to get the criteria ids
    $(".criterion:not(.blank, #criterion_1)").map((i,e)=>e.id.substring("criterion_".length))

# Acknowledgements
1. Nathan Self @nwself and https://community.canvaslms.com/thread/15580-how-can-one-get-the-criterion-id-from-an-api-call
1. Nathan Sprague @sprgunr and https://github.com/JMU-CS/Upload-Canvas-Grades
1. https://github.com/ucfopen/canvasapi