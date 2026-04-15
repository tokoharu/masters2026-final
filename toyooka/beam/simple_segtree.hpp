#pragma once
#ifndef SIMPLE_SEGTREE_HPP
#define SIMPLE_SEGTREE_HPP

#include <cassert>
#include <vector>

namespace simple_segtree_library
{
    template <class S, auto op, auto e>
    struct segtree
    {
    public:
        segtree() : segtree(0) {}

        explicit segtree(int n) : segtree(std::vector<S>(n, e())) {}

        explicit segtree(const std::vector<S> &v)
        {
            n_ = static_cast<int>(v.size());
            log_ = 0;
            while ((1U << log_) < static_cast<unsigned int>(n_))
            {
                ++log_;
            }
            size_ = 1 << log_;
            d_.assign(2 * size_, e());
            for (int i = 0; i < n_; ++i)
            {
                d_[size_ + i] = v[i];
            }
            for (int i = size_ - 1; i >= 1; --i)
            {
                update(i);
            }
        }

        void set(int p, const S &x)
        {
            assert(0 <= p && p < n_);
            p += size_;
            d_[p] = x;
            for (int i = 1; i <= log_; ++i)
            {
                update(p >> i);
            }
        }

        S get(int p) const
        {
            assert(0 <= p && p < n_);
            return d_[p + size_];
        }

        S prod(int l, int r) const
        {
            assert(0 <= l && l <= r && r <= n_);
            S sml = e();
            S smr = e();
            l += size_;
            r += size_;

            while (l < r)
            {
                if (l & 1)
                {
                    sml = op(sml, d_[l++]);
                }
                if (r & 1)
                {
                    smr = op(d_[--r], smr);
                }
                l >>= 1;
                r >>= 1;
            }
            return op(sml, smr);
        }

        S all_prod() const
        {
            return d_[1];
        }

    private:
        int n_;
        int size_;
        int log_;
        std::vector<S> d_;

        void update(int k)
        {
            d_[k] = op(d_[2 * k], d_[2 * k + 1]);
        }
    };
}

#endif
