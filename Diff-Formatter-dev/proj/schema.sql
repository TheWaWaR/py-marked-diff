drop table if exists files_diff_output;
create table files_diff_output (
       id integer not null autoincrement,
       filename1 text(200),
       filename1 text(200),
       result1 text,
       result2 text,
);
