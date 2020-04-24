package org.blagodarie.db;

import androidx.room.TypeConverter;

import java.util.UUID;

final class Converters {
    @TypeConverter
    public UUID StringToUuid (final String o) {
        return UUID.fromString(o);
    }

    @TypeConverter
    public String UuidToString (final UUID o) {
        return o.toString();
    }
}
