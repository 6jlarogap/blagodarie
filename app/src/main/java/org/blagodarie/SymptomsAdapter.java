package org.blagodarie;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.databinding.DataBindingUtil;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.RecyclerView;

import org.blagodarie.databinding.SymptomItemBinding;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
final class SymptomsAdapter
        extends RecyclerView.Adapter<SymptomsAdapter.SymptomViewHolder> {

    private List<DisplaySymptom> mDisplaySymptoms;

    @NonNull
    private final UserSymptomCreator mUserSymptomCreator;

    SymptomsAdapter (@NonNull final UserSymptomCreator userSymptomCreator) {
        mUserSymptomCreator = userSymptomCreator;
    }

    @NonNull
    @Override
    public SymptomViewHolder onCreateViewHolder (@NonNull ViewGroup parent, int viewType) {
        final LayoutInflater inflater = LayoutInflater.from(parent.getContext());
        final SymptomItemBinding binding = DataBindingUtil.inflate(inflater, R.layout.symptom_item, parent, false);
        return new SymptomViewHolder(binding);
    }

    @Override
    public void onBindViewHolder (@NonNull SymptomViewHolder holder, int position) {
        final DisplaySymptom displaySymptom = mDisplaySymptoms.get(position);
        if (displaySymptom != null) {
            holder.bind(displaySymptom, new View.OnClickListener() {
                @Override
                public void onClick (View v) {
                    final long timestamp = System.currentTimeMillis();
                    displaySymptom.setLastTimestamp(timestamp);
                    notifyItemChanged(position);
                    order();
                    mUserSymptomCreator.create(displaySymptom.getSymptom(), timestamp);
                }
            });
        }
    }

    @Override
    public int getItemCount () {
        return mDisplaySymptoms == null ? 0 : mDisplaySymptoms.size();
    }

    void setSymptoms (@NonNull final List<DisplaySymptom> displaySymptoms) {
        Collections.sort(displaySymptoms);
        final DiffUtil.DiffResult diffResult = DiffUtil.calculateDiff(new DisplaySymptomDiffUtilCallBack(displaySymptoms, mDisplaySymptoms));
        diffResult.dispatchUpdatesTo(this);
        mDisplaySymptoms = displaySymptoms;
    }

    private void order () {
        final List<DisplaySymptom> newDisplaySymptoms = new ArrayList<>(mDisplaySymptoms);
        setSymptoms(newDisplaySymptoms);
    }

    class SymptomViewHolder
            extends RecyclerView.ViewHolder {

        @NonNull
        private final SymptomItemBinding mBinding;

        SymptomViewHolder (@NonNull final SymptomItemBinding binding) {
            super(binding.getRoot());
            mBinding = binding;
        }

        void bind (
                @NonNull final DisplaySymptom displaySymptom,
                @NonNull final View.OnClickListener onClickListener
        ) {
            itemView.setOnClickListener(onClickListener);/*
            itemView.setOnClickListener(v -> {
                long timestamp = System.currentTimeMillis();
                displaySymptom.setLastTimestamp(timestamp);
                userSymptomCreator.create(displaySymptom.getSymptom(), timestamp);
                order();
            });*/
            mBinding.setDisplaySymptom(displaySymptom);
        }
    }

    private final class DisplaySymptomDiffUtilCallBack extends DiffUtil.Callback {

        final List<DisplaySymptom> mNewList;
        final List<DisplaySymptom> mOldList;

        public DisplaySymptomDiffUtilCallBack (
                final List<DisplaySymptom> newList,
                final List<DisplaySymptom> oldList
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
            return mNewList.get(newItemPosition).getSymptom().getId().equals(mOldList.get(oldItemPosition).getSymptom().getId());
        }

        @Override
        public boolean areContentsTheSame (int oldItemPosition, int newItemPosition) {
            final DisplaySymptom newItem = mNewList.get(newItemPosition);
            final DisplaySymptom oldItem = mOldList.get(newItemPosition);
            return newItem.getSymptom().equals(oldItem.getSymptom()) &&
                    (newItem.getLastTimestamp() == null ? oldItem.getLastTimestamp() == null : newItem.getLastTimestamp().equals(oldItem.getLastTimestamp()));
        }
    }
}