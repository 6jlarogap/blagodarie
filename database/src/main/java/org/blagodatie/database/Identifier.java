package org.blagodatie.database;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.util.Objects;

public final class Identifier
        implements Comparable<Identifier> {

    private static final Identifier NULL_ID = new Identifier(null);

    @Nullable
    private final Long mValue;

    Identifier (@Nullable final Long value) {
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

    @Override
    public int compareTo (@NonNull final Identifier o) {
        if (this.mValue != null) {
            if (o.mValue != null) {
                return this.mValue.compareTo(o.mValue);
            } else {
                return 1;
            }
        } else {
            if (o.mValue != null) {
                return -1;
            } else {
                return 0;
            }
        }
    }

}
