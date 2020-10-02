package blagodarie.health.database;

import androidx.annotation.NonNull;
import androidx.room.Embedded;
import androidx.room.Relation;

import java.util.Collections;
import java.util.List;

public final class MessageGroupWithMessages {

    @NonNull
    @Embedded
    private final MessageGroup MessageGroup;

    @NonNull
    @Relation (
            parentColumn = "id",
            entityColumn = "group_id",
            entity = Message.class
    )
    private final List<Message> mMessages;

    MessageGroupWithMessages (
            @NonNull final MessageGroup MessageGroup,
            @NonNull final List<Message> mMessages
    ) {
        this.MessageGroup = MessageGroup;
        this.mMessages = mMessages;
        //сортировать по Id
        Collections.sort(this.mMessages, (s1, s2) -> s1.getId().compareTo(s2.getId()));
    }

    @NonNull
    public final MessageGroup getMessageGroup () {
        return MessageGroup;
    }

    @NonNull
    public final List<Message> getmMessages () {
        return mMessages;
    }

    @Override
    public String toString () {
        return "MessageGroupWithMessages{" +
                "MessageGroup=" + MessageGroup +
                ", mMessages=" + mMessages +
                '}';
    }
}
