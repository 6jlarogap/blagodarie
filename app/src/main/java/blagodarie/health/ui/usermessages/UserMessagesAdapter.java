package blagodarie.health.ui.usermessages;

import android.view.LayoutInflater;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.databinding.DataBindingUtil;
import androidx.paging.PagedListAdapter;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.RecyclerView;

import java.util.Date;

import blagodarie.health.R;
import blagodarie.health.databinding.UserMessageItemBinding;

public final class UserMessagesAdapter
        extends PagedListAdapter<Date, UserMessagesAdapter.UserMessageViewHolder> {

    protected UserMessagesAdapter () {
        super(DIFF_CALLBACK);
    }

    @NonNull
    @Override
    public UserMessageViewHolder onCreateViewHolder (@NonNull ViewGroup parent, int viewType) {
        final LayoutInflater inflater = LayoutInflater.from(parent.getContext());
        final UserMessageItemBinding binding = DataBindingUtil.inflate(inflater, R.layout.user_message_item, parent, false);
        return new UserMessagesAdapter.UserMessageViewHolder(binding);
    }

    @Override
    public void onBindViewHolder (
            @NonNull UserMessageViewHolder holder,
            int position
    ) {
        final Date userMessage = getItem(position);
        if (userMessage != null) {
            holder.bind(userMessage);
        }
    }

    static final class UserMessageViewHolder
            extends RecyclerView.ViewHolder {

        @NonNull
        private final UserMessageItemBinding mBinding;

        UserMessageViewHolder (@NonNull final UserMessageItemBinding binding) {
            super(binding.getRoot());
            mBinding = binding;
        }

        void bind (
                @NonNull final Date date
        ) {
            mBinding.setUserMessage(date);
        }
    }

    private static DiffUtil.ItemCallback<Date> DIFF_CALLBACK =
            new DiffUtil.ItemCallback<Date>() {

                @Override
                public boolean areItemsTheSame (
                        Date oldItem,
                        Date newItem
                ) {
                    return false;
                }

                @Override
                public boolean areContentsTheSame (
                        Date oldOperation,
                        Date newOperation
                ) {
                    return false;
                }
            };
}
