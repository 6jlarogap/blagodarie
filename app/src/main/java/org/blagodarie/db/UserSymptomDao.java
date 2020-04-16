package org.blagodarie.db;

import androidx.annotation.NonNull;
import androidx.room.Dao;
import androidx.room.Insert;

@Dao
public abstract class UserSymptomDao {

    @Insert
    public abstract void insert (@NonNull UserSymptom userSymptom);

}
