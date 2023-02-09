# Scripts for Running the iChrisBirch Project

The scripts folder needs to be moved to:
`/usr/ubuntu/scripts`
and then all script files should be able to run from that directory.

Would be nice to use airflow or something to do these scripts.
 TODO: [2023/01/21] - Airflow vs Jenkins

Eventually it would be nice to make these universal so they could apply to any project on that server, by referencing the project name and directory (maybe this is where the global $PROJECT comes from) in the script as it is run.
Or possibly there is a way to create a special run (think python partial or spark-submit scripts) that does all of the stuff but has project name pre-populated and is named accordingly so that it is more explicit this script does this thing for that project, but references the universal script.
