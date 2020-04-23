package org.blagodarie.db;

import androidx.room.Dao;
import androidx.room.Insert;

@Dao
public abstract class UserSymptomKeyJoinDao {
    @Insert
    public abstract void insert (final UserSymptomKeyJoin userSymptomKeyJoin);
}
