package blagodarie.health.ui.messages;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.databinding.DataBindingUtil;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;
import java.util.List;

import blagodarie.health.R;
import blagodarie.health.databinding.MessageGroupItemBinding;

public final class MessageGroupsAdapter
        extends RecyclerView.Adapter<MessageGroupsAdapter.MessageGroupViewHolder> {

    @NonNull
    private final List<DisplayMessageGroup> mDisplayMessageGroups = new ArrayList<>();

    @NonNull
    private final MessageGroupClickListener mMessageGroupClickListener;

    MessageGroupsAdapter (
            @NonNull final List<DisplayMessageGroup> displayMessageGroups,
            @NonNull final MessageGroupClickListener messageGroupClickListener
    ) {
        mDisplayMessageGroups.addAll(displayMessageGroups);
        mMessageGroupClickListener = messageGroupClickListener;
    }

    @NonNull
    @Override
    public MessageGroupViewHolder onCreateViewHolder (
            @NonNull final ViewGroup parent,
            final int viewType
    ) {
        final LayoutInflater inflater = LayoutInflater.from(parent.getContext());
        final MessageGroupItemBinding binding = DataBindingUtil.inflate(inflater, R.layout.message_group_item, parent, false);
        return new MessageGroupViewHolder(binding);
    }

    @Override
    public void onBindViewHolder (
            @NonNull final MessageGroupViewHolder holder,
            final int position
    ) {
        final DisplayMessageGroup displayMessageGroup = mDisplayMessageGroups.get(position);
        if (displayMessageGroup != null) {
            holder.bind(displayMessageGroup, v -> {
                if (!displayMessageGroup.isSelected()) {
                    mMessageGroupClickListener.onClick(displayMessageGroup);
                }
            });
        }
    }

    @Override
    public int getItemCount () {
        return mDisplayMessageGroups.size();
    }

    void setData (@NonNull final List<DisplayMessageGroup> displayMessageGroups) {
        final DiffUtil.DiffResult diffResult = DiffUtil.calculateDiff(new DisplayMessageGroupDiffUtilCallBack(displayMessageGroups, mDisplayMessageGroups));
        diffResult.dispatchUpdatesTo(this);
        mDisplayMessageGroups.clear();
        mDisplayMessageGroups.addAll(displayMessageGroups);
    }

    static final class MessageGroupViewHolder
            extends RecyclerView.ViewHolder {

        @NonNull
        private final MessageGroupItemBinding mBinding;

        MessageGroupViewHolder (@NonNull final MessageGroupItemBinding binding) {
            super(binding.getRoot());
            mBinding = binding;
        }

        void bind (
                @NonNull final DisplayMessageGroup displayMessageGroup,
                @NonNull final View.OnClickListener onClickListener
        ) {
            itemView.setOnClickListener(onClickListener);
            mBinding.setDisplayMessageGroup(displayMessageGroup);
        }
    }

    private static final class DisplayMessageGroupDiffUtilCallBack
            extends DiffUtil.Callback {

        final List<DisplayMessageGroup> mNewList;
        final List<DisplayMessageGroup> mOldList;

        DisplayMessageGroupDiffUtilCallBack (
                final List<DisplayMessageGroup> newList,
                final List<DisplayMessageGroup> oldList
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
            final DisplayMessageGroup newItem = mNewList.get(newItemPosition);
            final DisplayMessageGroup oldItem = mOldList.get(newItemPosition);
            return newItem.equals(oldItem);
        }
    }
}
