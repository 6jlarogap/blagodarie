package org.blagodatie.database;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.util.Objects;

public final class Identifier {

    private static final Identifier NULL_ID = new Identifier(null);

    private final Long mValue;

    private Identifier (final Long value) {
        mValue = value;
    }

    static Identifier newInstance(@NonNull final Long value){
        return new Identifier(value);
    }

    @Nullable
    final Long getValue () {
        return mValue;
    }

    static Identifier getNullId () {
        return NULL_ID;
    }

    @Override
    public boolean equals (Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Identifier identificator = (Identifier) o;
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
