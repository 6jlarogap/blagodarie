package blagodarie.health.ui.messages;

import androidx.annotation.NonNull;
import androidx.databinding.BaseObservable;
import androidx.databinding.Bindable;

import java.util.List;

import blagodarie.health.database.Identifier;

public final class DisplayMessageGroup
        extends BaseObservable {

    @NonNull
    private final Identifier mMessageGroupId;

    @NonNull
    private final String mMessageGroupName;

    @NonNull
    private final List<DisplayMessage> mDisplayMessages;

    private boolean mSelected = false;

    DisplayMessageGroup (
            @NonNull final Identifier messageGroupId,
            @NonNull final String messageGroupName,
            @NonNull final List<DisplayMessage> displayMessages
    ) {
        mMessageGroupId = messageGroupId;
        mMessageGroupName = messageGroupName;
        mDisplayMessages = displayMessages;
    }

    @NonNull
    Identifier getMessageGroupId () {
        return mMessageGroupId;
    }

    @NonNull
    public String getMessageGroupName () {
        return mMessageGroupName;
    }

    @NonNull
    List<DisplayMessage> getDisplayMessages () {
        return mDisplayMessages;
    }

    @Bindable
    public boolean isSelected () {
        return mSelected;
    }

    void setSelected (final boolean selected) {
        mSelected = selected;
        notifyPropertyChanged(blagodarie.health.BR.selected);
    }

    long getUserMessageCount () {
        long userMessageCount = 0;
        for (DisplayMessage displayMessage : mDisplayMessages) {
            userMessageCount += displayMessage.getUserMessageCount();
        }
        return userMessageCount;
    }

    @Override
    public String toString () {
        return "DisplayMessageGroup{" +
                "mMessageGroupId=" + mMessageGroupId +
                ", mMessageGroupName='" + mMessageGroupName + '\'' +
                ", mDisplayMessages=" + mDisplayMessages +
                ", mSelected=" + mSelected +
                '}';
    }
}
