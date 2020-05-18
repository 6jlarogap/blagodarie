package org.blagodarie.ui.symptoms;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.databinding.DataBindingUtil;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.RecyclerView;

import org.blagodarie.R;
import org.blagodarie.databinding.SymptomGroupItemBinding;

import java.util.ArrayList;
import java.util.List;

public class SymptomGroupsAdapter
        extends RecyclerView.Adapter<SymptomGroupsAdapter.SymptomGroupViewHolder> {

    @NonNull
    private final List<DisplaySymptomGroup> mDisplaySymptomGroups = new ArrayList<>();

    @NonNull
    private final SymptomGroupClickListener mSymptomGroupClickListener;

    SymptomGroupsAdapter (
            @NonNull final List<DisplaySymptomGroup> displaySymptomGroups,
            @NonNull final SymptomGroupClickListener symptomGroupClickListener
    ) {
        mDisplaySymptomGroups.addAll(displaySymptomGroups);
        mSymptomGroupClickListener = symptomGroupClickListener;
    }

    @NonNull
    @Override
    public SymptomGroupViewHolder onCreateViewHolder (
            @NonNull final ViewGroup parent,
            final int viewType
    ) {
        final LayoutInflater inflater = LayoutInflater.from(parent.getContext());
        final SymptomGroupItemBinding binding = DataBindingUtil.inflate(inflater, R.layout.symptom_group_item, parent, false);
        return new SymptomGroupViewHolder(binding);
    }

    @Override
    public void onBindViewHolder (
            @NonNull final SymptomGroupViewHolder holder,
            final int position
    ) {
        final DisplaySymptomGroup displaySymptomGroup = mDisplaySymptomGroups.get(position);
        if (displaySymptomGroup != null) {
            holder.bind(displaySymptomGroup, v -> {
                if (!displaySymptomGroup.isSelected()) {
                    mSymptomGroupClickListener.onClick(displaySymptomGroup);
                }
            });
        }
    }

    @Override
    public int getItemCount () {
        return mDisplaySymptomGroups.size();
    }

    void setData (@NonNull final List<DisplaySymptomGroup> displaySymptomGroups) {
        final DiffUtil.DiffResult diffResult = DiffUtil.calculateDiff(new DisplaySymptomGroupDiffUtilCallBack(displaySymptomGroups, mDisplaySymptomGroups));
        diffResult.dispatchUpdatesTo(this);
        mDisplaySymptomGroups.clear();
        mDisplaySymptomGroups.addAll(displaySymptomGroups);
    }

    static final class SymptomGroupViewHolder
            extends RecyclerView.ViewHolder {

        @NonNull
        private final SymptomGroupItemBinding mBinding;

        SymptomGroupViewHolder (@NonNull final SymptomGroupItemBinding binding) {
            super(binding.getRoot());
            mBinding = binding;
        }

        void bind (
                @NonNull final DisplaySymptomGroup displaySymptomGroup,
                @NonNull final View.OnClickListener onClickListener
        ) {
            itemView.setOnClickListener(onClickListener);
            mBinding.setDisplaySymptomGroup(displaySymptomGroup);
        }
    }

    private static final class DisplaySymptomGroupDiffUtilCallBack
            extends DiffUtil.Callback {

        final List<DisplaySymptomGroup> mNewList;
        final List<DisplaySymptomGroup> mOldList;

        DisplaySymptomGroupDiffUtilCallBack (
                final List<DisplaySymptomGroup> newList,
                final List<DisplaySymptomGroup> oldList
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
            final DisplaySymptomGroup newItem = mNewList.get(newItemPosition);
            final DisplaySymptomGroup oldItem = mOldList.get(newItemPosition);
            return newItem.equals(oldItem);
        }
    }
}
