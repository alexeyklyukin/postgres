# This test checks that multiple sessions locking a single row in a table
# does not deadlock each other, particularly when one of them upgrades its
# lock while the others are waiting.

setup
{
    drop table if exists tlu_job;
    create table tlu_job (id integer primary key, name text);

    insert into tlu_job values(1, 'a');
}


teardown
{
    drop table tlu_job;
}

session "s1"
setup { begin; }
step "s1_keyshare" { select id from tlu_job where id = 1 for key share;}    
step "s1_share" { select id from tlu_job where id = 1 for share; }
step "s1_update" { update tlu_job set name = 'b' where id = 1;  }
step "s1_delete" { delete from tlu_job where id = 1; }
step "s1_rollback" { rollback; }

session "s2"
setup { begin; }
step "s2_for_update" { select id from tlu_job where id = 1 for update; }
step "s2_rollback" { rollback; }

session "s3"
setup { begin; }
step "s3_keyshare" { select id from tlu_job where id = 1 for key share; }
step "s3_share" { select id from tlu_job where id = 1 for share; }
step "s3_for_update" { select id from tlu_job where id = 1 for update; }
step "s3_update" { update tlu_job set name = 'b' where id = 1; }
step "s3_delete" { delete from tlu_job where id = 1; }
step "s3_rollback" { rollback; }

# test that s2 will not deadlock with s3 when s1 is rolled back
permutation "s1_share" "s2_for_update" "s3_share" "s3_for_update" "s1_rollback" "s3_rollback" "s2_rollback"
# test that update does not cause deadlocks if it can proceed
permutation  "s1_keyshare" "s2_for_update" "s3_keyshare" "s1_update" "s3_update" "s1_rollback" "s3_rollback" "s2_rollback"
# test that delete does not cause deadlocks if it can proceed
permutation "s1_keyshare" "s2_for_update" "s3_keyshare"  "s3_delete" "s1_rollback" "s3_rollback" "s2_rollback"

