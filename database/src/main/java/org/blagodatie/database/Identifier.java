package org.blagodatie.database;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.util.Objects;

public final class Identifier {

    private static final Identifier NULL_ID = new Identifier(null);

    @Nullable
    private final Long mValue;

    private Identifier (@Nullable final Long value) {
        mValue = value;
    }

    @NonNull
    public static Identifier newInstance (@Nullable final Long value) {
        return value != null ? new Identifier(value) : NULL_ID;
    }

    @Nullable
    final Long getValue () {
        return mValue;
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        final Identifier identificator = (Identifier) o;
        return Objects.equals(mValue, identificator.mValue);
    }

    @Override
    public int hashCode () {
        return Objects.hash(mValue);
    }

    @NonNull
    @Override
    public String toString () {
        return mValue != null ? mValue.toString() : "null";
    }
}
