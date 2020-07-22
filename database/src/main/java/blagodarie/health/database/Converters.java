package blagodarie.health.database;

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

    @TypeConverter
    public Identifier longToIdentifier (final Long o) {
        return Identifier.newInstance(o);
    }

    @TypeConverter
    public Long identifierToLong (@NonNull final Identifier o) {
        return o.getValue();
    }

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
        return new SimpleDateFormat(DATE_STRING_FORMAT, Locale.ENGLISH).format(o);
    }

    @Nullable
    @TypeConverter
    public Date stringToDate (@NonNull final String o) {
        try {
            return new SimpleDateFormat(DATE_STRING_FORMAT, Locale.ENGLISH).parse(o);
        } catch (ParseException e) {
            Log.e(TAG, "stringToDate error=" + e);
            return null;
        }
    }
}
