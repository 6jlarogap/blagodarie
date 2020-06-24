package blagodarie.health.ui.messages;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.databinding.DataBindingUtil;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.RecyclerView;

import blagodarie.health.R;
import blagodarie.health.databinding.MessageItemBinding;

import java.util.ArrayList;
import java.util.List;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
final class MessagesAdapter
        extends RecyclerView.Adapter<MessagesAdapter.MessageViewHolder> {

    @NonNull
    private final List<DisplayMessage> mDisplayMessages = new ArrayList<>();

    @NonNull
    private final DisplayMessageClickListener mDisplayMessageClickListener;

    MessagesAdapter (
            @NonNull final List<DisplayMessage> displayMessages,
            @NonNull final DisplayMessageClickListener displayMessageClickListener
    ) {
        mDisplayMessages.addAll(displayMessages);
        mDisplayMessageClickListener = displayMessageClickListener;
    }

    @NonNull
    @Override
    public MessageViewHolder onCreateViewHolder (@NonNull ViewGroup parent, int viewType) {
        final LayoutInflater inflater = LayoutInflater.from(parent.getContext());
        final MessageItemBinding binding = DataBindingUtil.inflate(inflater, R.layout.message_item, parent, false);
        return new MessageViewHolder(binding);
    }

    @Override
    public void onBindViewHolder (@NonNull MessageViewHolder holder, int position) {
        final DisplayMessage displayMessage = mDisplayMessages.get(position);
        if (displayMessage != null) {
            holder.bind(displayMessage, v -> {
                if (!displayMessage.isHighlight()) {
                    mDisplayMessageClickListener.onClick(displayMessage);
                }
            });
        }
    }

    @Override
    public int getItemCount () {
        return mDisplayMessages.size();
    }

    final void setData (@NonNull final List<DisplayMessage> displayMessages) {
        final DiffUtil.DiffResult diffResult = DiffUtil.calculateDiff(new DisplayMessageDiffUtilCallBack(displayMessages, mDisplayMessages));
        diffResult.dispatchUpdatesTo(this);
        mDisplayMessages.clear();
        mDisplayMessages.addAll(displayMessages);
    }

    static final class MessageViewHolder
            extends RecyclerView.ViewHolder {

        @NonNull
        private final MessageItemBinding mBinding;

        MessageViewHolder (@NonNull final MessageItemBinding binding) {
            super(binding.getRoot());
            mBinding = binding;
        }

        void bind (
                @NonNull final DisplayMessage displayMessage,
                @NonNull final View.OnClickListener onClickListener
        ) {
            itemView.setOnClickListener(onClickListener);
            mBinding.setDisplayMessage(displayMessage);
        }
    }

    private static final class DisplayMessageDiffUtilCallBack
            extends DiffUtil.Callback {

        final List<DisplayMessage> mNewList;
        final List<DisplayMessage> mOldList;

        DisplayMessageDiffUtilCallBack (
                final List<DisplayMessage> newList,
                final List<DisplayMessage> oldList
        ) {
            this.mNewList = newList;
            this.mOldList = oldList;
        }

        @Override
        public int getOldListSize () {
            return mOldList != null ? mOldList.size() : 0;
        }

        @Override
        public int getNewListSize () {
            return mNewList != null ? mNewList.size() : 0;
        }

        @Override
        public boolean areItemsTheSame (int oldItemPosition, int newItemPosition) {
            return mNewList.get(newItemPosition).equals(mOldList.get(oldItemPosition));
        }

        @Override
        public boolean areContentsTheSame (int oldItemPosition, int newItemPosition) {
            final DisplayMessage newItem = mNewList.get(newItemPosition);
            final DisplayMessage oldItem = mOldList.get(newItemPosition);
            return newItem.equals(oldItem);
        }
    }
}
