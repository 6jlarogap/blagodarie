package org.blagodatie.database;

import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.TypeConverter;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.UUID;

final class Converters {

    private static final String TAG = Converters.class.getSimpleName();

    private static final String DATE_STRING_FORMAT = "yyyy-MM-dd HH:mm:ss.SSSZ";
    private static final SimpleDateFormat DATE_FORMAT = new SimpleDateFormat(DATE_STRING_FORMAT, Locale.ENGLISH);

    @TypeConverter
    public UUID stringToUuid (@NonNull final String o) {
        return UUID.fromString(o);
    }

    @TypeConverter
    public String uuidToString (@NonNull final UUID o) {
        return o.toString();
    }

    @TypeConverter
    public String dateToString (@NonNull final Date o) {
        return DATE_FORMAT.format(o);
    }

    @Nullable
    @TypeConverter
    public Date stringToDate (@NonNull final String o) {
        try {
            return DATE_FORMAT.parse(o);
        } catch (ParseException e) {
            Log.e(TAG, "stringToDate error=" + e);
            return null;
        }
    }
}
