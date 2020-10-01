package blagodarie.health.ui.usermessages;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.ViewModel;
import androidx.paging.PagedList;

import java.util.Date;

public final class UserMessagesViewModel
        extends ViewModel {

    private LiveData<PagedList<Date>> mUserMessages;

    public LiveData<PagedList<Date>> getUserMessages () {
        return mUserMessages;
    }

    public void setUserMessages (LiveData<PagedList<Date>> userMessages) {
        mUserMessages = userMessages;
    }
}
