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
import java.util.List;

/**
 * @author sergeGabrus
 * @link https://github.com/6jlarogap/blagodarie/blob/master/LICENSE License
 */
final class SymptomsAdapter
        extends RecyclerView.Adapter<SymptomsAdapter.SymptomViewHolder> {

    @NonNull
    private List<DisplaySymptom> mDisplaySymptoms;

    @NonNull
    private final DisplaySymptomClickListener mDisplaySymptomClickListener;

    SymptomsAdapter (
            @NonNull final List<DisplaySymptom> displaySymptoms,
            @NonNull final DisplaySymptomClickListener displaySymptomClickListener
    ) {
        mDisplaySymptoms = displaySymptoms;
        mDisplaySymptomClickListener = displaySymptomClickListener;
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
            holder.bind(displaySymptom, v -> {
                if (!displaySymptom.getInLoadProgress().get() &&
                        !displaySymptom.getHighlight().get()) {
                    mDisplaySymptomClickListener.onClick(displaySymptom);
                }
            });
        }
    }

    @Override
    public int getItemCount () {
        return mDisplaySymptoms.size();
    }

    private void order () {
        final List<DisplaySymptom> newDisplaySymptoms = new ArrayList<>(mDisplaySymptoms);
        //Collections.sort(newDisplaySymptoms);
        final DiffUtil.DiffResult diffResult = DiffUtil.calculateDiff(new DisplaySymptomDiffUtilCallBack(newDisplaySymptoms, mDisplaySymptoms));
        diffResult.dispatchUpdatesTo(this);
        mDisplaySymptoms = newDisplaySymptoms;
    }

    static final class SymptomViewHolder
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
                userSymptomCreator.onClick(displaySymptom.getSymptom(), timestamp);
                order();
            });*/
            mBinding.setDisplaySymptom(displaySymptom);
        }
    }

    private static final class DisplaySymptomDiffUtilCallBack
            extends DiffUtil.Callback {

        final List<DisplaySymptom> mNewList;
        final List<DisplaySymptom> mOldList;

        DisplaySymptomDiffUtilCallBack (
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
            return mNewList.get(newItemPosition).getSymptomId().equals(mOldList.get(oldItemPosition).getSymptomId());
        }

        @Override
        public boolean areContentsTheSame (int oldItemPosition, int newItemPosition) {
            final DisplaySymptom newItem = mNewList.get(newItemPosition);
            final DisplaySymptom oldItem = mOldList.get(newItemPosition);
            return newItem.getSymptomId().equals(oldItem.getSymptomId()) &&
                    (newItem.getLastAdd() == null ? oldItem.getLastAdd() == null : newItem.getLastAdd().equals(oldItem.getLastAdd()));
        }
    }
}
