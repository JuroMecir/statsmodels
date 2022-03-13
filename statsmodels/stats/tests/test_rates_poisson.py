

import pytest
import warnings
from numpy import arange
from numpy.testing import assert_allclose, assert_equal

# we cannot import test_poisson_2indep directly, pytest treats that as test
import statsmodels.stats.rates as smr
from statsmodels.stats.rates import (
    # test_poisson, # cannot import functions that start with test
    confint_poisson,
    etest_poisson_2indep,
    power_poisson_2indep,
    power_equivalence_poisson_2indep,
    power_poisson_diff_2indep,
    )


methods = ["wald", "score", "exact-c", "waldccv", "sqrt-a", "sqrt-v", "midp-c",
           ]


@pytest.mark.parametrize('method', methods)
def test_rate_poisson_consistency(method):
    # check consistency between test and confint for one poisson rate
    count, nobs = 15, 400
    ci = confint_poisson(count, nobs, method=method)
    pv1 = smr.test_poisson(count, nobs, value=ci[0], method=method).pvalue
    pv2 = smr.test_poisson(count, nobs, value=ci[1], method=method).pvalue

    rtol = 1e-10
    if method in ["midp-c"]:
        # numerical root finding, lower precision
        rtol = 1e-6
    assert_allclose(pv1, 0.05, rtol=rtol)
    assert_allclose(pv2, 0.05, rtol=rtol)

    # check one-sided, note all confint are central
    pv1 = smr.test_poisson(count, nobs, value=ci[0], method=method,
                           alternative="larger").pvalue
    pv2 = smr.test_poisson(count, nobs, value=ci[1], method=method,
                           alternative="smaller").pvalue

    assert_allclose(pv1, 0.025, rtol=rtol)
    assert_allclose(pv2, 0.025, rtol=rtol)


def test_rate_poisson_r():
    count, nobs = 15, 400

    # DescTools
    # PoissonCI(x=15, n=400, method = c("exact","score", "wald", "byar"))
    # exact 0.0375 0.0209884653319583 0.0618505471787146
    # score 0.0375 0.0227264749053794 0.0618771721463559
    # wald  0.0375 0.0185227303217751 0.0564772696782249
    # byar  0.0375 0.0219084369245707 0.0602933510943048


    # > rr = poisson.exact(15, 400, r=0.05, tsmethod="central")
    # > rr$p.value
    # > rr$conf.int
    pv2 = 0.313026269279486
    ci2 = (0.0209884653319583, 0.0618505471787146)
    rt = smr.test_poisson(count, nobs, value=0.05, method="exact-c")
    ci = confint_poisson(count, nobs, method="exact-c")
    assert_allclose(rt.pvalue, pv2, rtol=1e-12)
    assert_allclose(ci, ci2, rtol=1e-12)

    # R package ratesci
    # sr = scoreci(15, 400, contrast="p", distrib = "poi", skew=FALSE,
    #      theta0=0.05)
    # pval computed from 2 * min(pval_left, pval_right)
    pv2 = 0.263552477282973
    # ci2 = (0.022726, 0.061877)  # no additional digits available
    ci2 = (0.0227264749053794, 0.0618771721463559)  # from DescTools
    rt = smr.test_poisson(count, nobs, value=0.05, method="score")
    ci = confint_poisson(count, nobs, method="score")
    assert_allclose(rt.pvalue, pv2, rtol=1e-12)
    assert_allclose(ci, ci2, rtol=1e-12)

    # > jeffreysci(15, 400, distrib = "poi")
    ci2 = (0.0219234232268444, 0.0602898619930649)
    ci = confint_poisson(count, nobs, method="jeff")
    assert_allclose(ci, ci2, rtol=1e-12)

    # from DescTools
    ci2 = (0.0185227303217751, 0.0564772696782249)
    ci = confint_poisson(count, nobs, method="wald")
    assert_allclose(ci, ci2, rtol=1e-12)

    # from ratesci
    # rateci(15, 400, distrib = "poi")
    # I think their lower ci is wrong, it also doesn't match for exact_c
    ci2 = (0.0243357599260795, 0.0604627555786095)
    ci = confint_poisson(count, nobs, method="midp-c")
    assert_allclose(ci[1], ci2[1], rtol=1e-5)


def test_twosample_poisson():
    # testing against two examples in Gu et al

    # example 1
    count1, n1, count2, n2 = 60, 51477.5, 30, 54308.7

    s1, pv1 = smr.test_poisson_2indep(count1, n1, count2, n2, method='wald')
    pv1r = 0.000356
    assert_allclose(pv1, pv1r*2, rtol=0, atol=5e-6)
    assert_allclose(s1, 3.384913, atol=0, rtol=5e-6)  # regression test

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2, method='score')
    pv2r = 0.000316
    assert_allclose(pv2, pv2r*2, rtol=0, atol=5e-6)
    assert_allclose(s2, 3.417402, atol=0, rtol=5e-6)  # regression test

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2, method='sqrt')
    pv2r = 0.000285
    assert_allclose(pv2, pv2r*2, rtol=0, atol=5e-6)
    assert_allclose(s2, 3.445485, atol=0, rtol=5e-6)  # regression test

    # two-sided
    # example2
    # I don't know why it's only 2.5 decimal agreement, rounding?
    count1, n1, count2, n2 = 41, 28010, 15, 19017
    s1, pv1 = smr.test_poisson_2indep(count1, n1, count2, n2, method='wald',
                                      ratio_null=1.5)
    pv1r = 0.2309
    assert_allclose(pv1, pv1r*2, rtol=0, atol=5e-3)
    assert_allclose(s1, 0.735447, atol=0, rtol=5e-6)  # regression test

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2, method='score',
                                      ratio_null=1.5)
    pv2r = 0.2398
    assert_allclose(pv2, pv2r*2, rtol=0, atol=5e-3)
    assert_allclose(s2, 0.706631, atol=0, rtol=5e-6)  # regression test

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2, method='sqrt',
                                      ratio_null=1.5)
    pv2r = 0.2499
    assert_allclose(pv2, pv2r*2, rtol=0, atol=5e-3)
    assert_allclose(s2, 0.674401, atol=0, rtol=5e-6)  # regression test

    # one-sided
    # example 1 onesided
    count1, n1, count2, n2 = 60, 51477.5, 30, 54308.7

    s1, pv1 = smr.test_poisson_2indep(count1, n1, count2, n2, method='wald',
                                      alternative='larger')
    pv1r = 0.000356
    assert_allclose(pv1, pv1r, rtol=0, atol=5e-6)

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2, method='score',
                                      alternative='larger')
    pv2r = 0.000316
    assert_allclose(pv2, pv2r, rtol=0, atol=5e-6)

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2, method='sqrt',
                                      alternative='larger')
    pv2r = 0.000285
    assert_allclose(pv2, pv2r, rtol=0, atol=5e-6)

    # 'exact-cond', 'cond-midp'

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2,
                                      method='exact-cond',
                                      ratio_null=1, alternative='larger')
    pv2r = 0.000428  # typo in Gu et al, switched pvalues between C and M
    assert_allclose(pv2, pv2r, rtol=0, atol=5e-4)

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2,
                                      method='cond-midp',
                                      ratio_null=1, alternative='larger')
    pv2r = 0.000310
    assert_allclose(pv2, pv2r, rtol=0, atol=5e-4)

    _, pve1 = etest_poisson_2indep(count1, n1, count2, n2,
                                   method='score',
                                   ratio_null=1, alternative='larger')
    pve1r = 0.000298
    assert_allclose(pve1, pve1r, rtol=0, atol=5e-4)

    _, pve1 = etest_poisson_2indep(count1, n1, count2, n2,
                                   method='wald',
                                   ratio_null=1, alternative='larger')
    pve1r = 0.000298
    assert_allclose(pve1, pve1r, rtol=0, atol=5e-4)

    # example2 onesided
    # I don't know why it's only 2.5 decimal agreement, rounding?
    count1, n1, count2, n2 = 41, 28010, 15, 19017
    s1, pv1 = smr.test_poisson_2indep(count1, n1, count2, n2, method='wald',
                                      ratio_null=1.5, alternative='larger')
    pv1r = 0.2309
    assert_allclose(pv1, pv1r, rtol=0, atol=5e-4)

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2, method='score',
                                      ratio_null=1.5, alternative='larger')
    pv2r = 0.2398
    assert_allclose(pv2, pv2r, rtol=0, atol=5e-4)

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2, method='sqrt',
                                      ratio_null=1.5, alternative='larger')
    pv2r = 0.2499
    assert_allclose(pv2, pv2r, rtol=0, atol=5e-4)

    # 'exact-cond', 'cond-midp'

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2,
                                      method='exact-cond',
                                      ratio_null=1.5, alternative='larger')
    pv2r = 0.2913
    assert_allclose(pv2, pv2r, rtol=0, atol=5e-4)

    s2, pv2 = smr.test_poisson_2indep(count1, n1, count2, n2,
                                      method='cond-midp',
                                      ratio_null=1.5, alternative='larger')
    pv2r = 0.2450
    assert_allclose(pv2, pv2r, rtol=0, atol=5e-4)

    _, pve2 = etest_poisson_2indep(count1, n1, count2, n2,
                                   method='score',
                                   ratio_null=1.5, alternative='larger')
    pve2r = 0.2453
    assert_allclose(pve2, pve2r, rtol=0, atol=5e-4)

    _, pve2 = etest_poisson_2indep(count1, n1, count2, n2,
                                   method='wald',
                                   ratio_null=1.5, alternative='larger')
    pve2r = 0.2453
    assert_allclose(pve2, pve2r, rtol=0, atol=5e-4)


def test_twosample_poisson_r():
    # testing against R package `exactci
    from .results.results_rates import res_pexact_cond, res_pexact_cond_midp

    # example 1 from Gu
    count1, n1, count2, n2 = 60, 51477.5, 30, 54308.7

    res2 = res_pexact_cond
    res1 = smr.test_poisson_2indep(count1, n1, count2, n2, method='exact-cond')
    assert_allclose(res1.pvalue, res2.p_value, rtol=1e-13)
    assert_allclose(res1.ratio, res2.estimate, rtol=1e-13)
    assert_equal(res1.ratio_null, res2.null_value)

    res2 = res_pexact_cond_midp
    res1 = smr.test_poisson_2indep(count1, n1, count2, n2, method='cond-midp')
    assert_allclose(res1.pvalue, res2.p_value, rtol=0, atol=5e-6)
    assert_allclose(res1.ratio, res2.estimate, rtol=1e-13)
    assert_equal(res1.ratio_null, res2.null_value)

    # one-sided
    # > pe = poisson.exact(c(60, 30), c(51477.5, 54308.7), r=1.2,
    #                      alternative="less", tsmethod="minlike", midp=TRUE)
    # > pe$p.value
    pv2 = 0.9949053964701466
    rest = smr.test_poisson_2indep(count1, n1, count2, n2, method='cond-midp',
                                   ratio_null=1.2, alternative='smaller')
    assert_allclose(rest.pvalue, pv2, rtol=1e-12)
    # > pe = poisson.exact(c(60, 30), c(51477.5, 54308.7), r=1.2,
    #           alternative="greater", tsmethod="minlike", midp=TRUE)
    # > pe$p.value
    pv2 = 0.005094603529853279
    rest = smr.test_poisson_2indep(count1, n1, count2, n2, method='cond-midp',
                                   ratio_null=1.2, alternative='larger')
    assert_allclose(rest.pvalue, pv2, rtol=1e-12)
    # > pe = poisson.exact(c(60, 30), c(51477.5, 54308.7), r=1.2,
    #           alternative="greater", tsmethod="minlike", midp=FALSE)
    # > pe$p.value
    pv2 = 0.006651774552714537
    rest = smr.test_poisson_2indep(count1, n1, count2, n2, method='exact-cond',
                                   ratio_null=1.2, alternative='larger')
    assert_allclose(rest.pvalue, pv2, rtol=1e-12)
    # > pe = poisson.exact(c(60, 30), c(51477.5, 54308.7), r=1.2,
    #                      alternative="less", tsmethod="minlike", midp=FALSE)
    # > pe$p.value
    pv2 = 0.9964625674930079
    rest = smr.test_poisson_2indep(count1, n1, count2, n2, method='exact-cond',
                                   ratio_null=1.2, alternative='smaller')
    assert_allclose(rest.pvalue, pv2, rtol=1e-12)


def test_tost_poisson():

    count1, n1, count2, n2 = 60, 51477.5, 30, 54308.7
    # # central conf_int from R exactci
    low, upp = 1.339735721772650, 3.388365573616252

    res = smr.tost_poisson_2indep(count1, n1, count2, n2, low, upp,
                                  method="exact-cond")

    assert_allclose(res.pvalue, 0.025, rtol=1e-12)
    methods = ['wald', 'score', 'sqrt', 'exact-cond', 'cond-midp']

    # test that we are in the correct range for other methods
    for meth in methods:
        res = smr.tost_poisson_2indep(count1, n1, count2, n2, low, upp,
                                      method=meth)
        assert_allclose(res.pvalue, 0.025, atol=0.01)


cases_alt = {
    ("two-sided", "wald"): 0.07136366497984171,
    ("two-sided", "score"): 0.0840167525117227,
    ("two-sided", "sqrt"): 0.0804675114297235,
    ("two-sided", "exact-cond"): 0.1301269270479679,
    ("two-sided", "cond-midp"): 0.09324590196774807,
    ("two-sided", "etest"): 0.09054824785458056,
    ("two-sided", "etest-wald"): 0.06895289560607239,

    ("larger", "wald"): 0.03568183248992086,
    ("larger", "score"): 0.04200837625586135,
    ("larger", "sqrt"): 0.04023375571486175,
    ("larger", "exact-cond"): 0.08570447732927276,
    ("larger", "cond-midp"): 0.04882345224905293,
    ("larger", "etest"): 0.043751060642682936,
    ("larger", "etest-wald"): 0.043751050280207024,

    ("smaller", "wald"): 0.9643181675100791,
    ("smaller", "score"): 0.9579916237441386,
    ("smaller", "sqrt"): 0.9597662442851382,
    ("smaller", "exact-cond"): 0.9880575728311669,
    ("smaller", "cond-midp"): 0.9511765477509471,
    ("smaller", "etest"): 0.9672396898656999,
    ("smaller", "etest-wald"): 0.9672397002281757
    }


@pytest.mark.parametrize('case', list(cases_alt.keys()))
def test_alternative(case):
    # regression test numbers, but those are close to each other
    alt, meth = case
    count1, n1, count2, n2 = 6, 51., 1, 54.
    _, pv = smr.test_poisson_2indep(count1, n1, count2, n2, method=meth,
                                    ratio_null=1.2, alternative=alt)
    assert_allclose(pv, cases_alt[case], rtol=1e-13)


def test_y_grid_regression():
    y_grid = arange(1000)

    _, pv = etest_poisson_2indep(60, 51477.5, 30, 54308.7, y_grid=y_grid)
    assert_allclose(pv, 0.000567261758250953, atol=1e-15)

    _, pv = etest_poisson_2indep(41, 28010, 15, 19017, y_grid=y_grid)
    assert_allclose(pv, 0.03782053187021494, atol=1e-15)

    _, pv = etest_poisson_2indep(1, 1, 1, 1, y_grid=[1])
    assert_allclose(pv, 0.1353352832366127, atol=1e-15)


def test_invalid_y_grid():
    # check ygrid deprecation
    warnings.simplefilter("always")
    with warnings.catch_warnings(record=True) as w:
        etest_poisson_2indep(1, 1, 1, 1, ygrid=[1])
    assert len(w) == 1
    assert issubclass(w[0].category, DeprecationWarning)
    assert "ygrid" in str(w[0].message)

    # check y_grid validity
    with pytest.raises(ValueError) as e:
        etest_poisson_2indep(1, 1, 1, 1, y_grid=1)
    assert "y_grid" in str(e.value)


def test_poisson_power_2ratio():
    # power compared to PASS documentation

    rate1, rate2 = 2.2, 2.2
    nobs1, nobs2 = 95, 95
    nobs_ratio = 1
    alpha = 0.025
    exposure = 2.5
    low, upp = 0.8, 1.25
    dispersion = 1

    # check power of equivalence test
    cases = [
        (1.9, 704, 704, 0.90012),
        (2.0, 246, 246, 0.90057),
        (2.2, 95, 95, 0.90039),
        (2.5, 396, 396, 0.90045),
    ]

    for case in cases:
        rate1, nobs1, nobs2, p = case
        pow_ = power_equivalence_poisson_2indep(
            rate1, nobs1, rate2, nobs2, exposure, low, upp, alpha=alpha,
            dispersion=dispersion)
        assert_allclose(pow_, p, atol=5e-5)

    # check power of onesided test, smaller with a margin
    # non-inferiority
    # alternative smaller H1: rate1 / rate2 < R
    cases = [
        (1.8, 29, 29, 0.90056),
        (1.9, 39, 39, 0.90649),
        (2.2, 115, 115, 0.90014),
        (2.4, 404, 404, 0.90064),
    ]

    low = 1.2
    for case in cases:
        rate1, nobs1, nobs2, p = case
        pow_ = power_poisson_2indep(rate1, nobs1, rate2, nobs2, exposure,
                                    value=low, alpha=0.025, dispersion=1,
                                    alternative="smaller")

        assert_allclose(pow_, p, atol=5e-5)

        pow_ = power_poisson_2indep(
            rate1, nobs1, rate2, nobs2, exposure, value=low, alpha=0.05,
            dispersion=1, alternative="two-sided")
        assert_allclose(pow_, p, atol=5e-5)

    # check size, power at null
    pow_ = power_poisson_2indep(
            rate1, nobs1, rate2, nobs2, exposure, value=rate1 / rate2,
            alpha=0.05, dispersion=1, alternative="two-sided")
    assert_allclose(pow_, 0.05, atol=5e-5)

    # check power of onesided test, larger with a margin (superiority)
    # alternative larger H1: rate1 / rate2 > R
    # here I just reverse the case of smaller alternative

    cases = [
        (1.8, 29, 29, 0.90056),
        (1.9, 39, 39, 0.90649),
        (2.2, 115, 115, 0.90014),
        (2.4, 404, 404, 0.90064),
    ]

    rate1 = 2.2
    low = 1 / 1.2
    for case in cases:
        rate2, nobs1, nobs2, p = case
        pow_ = power_poisson_2indep(
            rate1, nobs1, rate2, nobs2, exposure, value=low, alpha=0.025,
            dispersion=1, alternative="larger")
        assert_allclose(pow_, p, atol=5e-5)

        pow_ = power_poisson_2indep(
            rate1, nobs1, rate2, nobs2, exposure, value=low, alpha=0.05,
            dispersion=1, alternative="two-sided")
        assert_allclose(pow_, p, atol=5e-5)


def test_power_poisson_equal():

    # Example from Chapter 436: Tests for the Difference Between Two Poisson
    # Rates
    # equality null H0: rate1 = rate2
    #
    # Power N1 N2 N rate1 rate2 diff(rate2-rate1) ratio(rate2/rate1) Alpha
    # 0.82566 8 6 14 10.00 15.00 5.00 1.5000 0.050
    #
    # "1" is reference group
    # we use group 2 reference

    nobs1, nobs2 = 6, 8
    nobs_ratio = nobs1 / nobs2
    rate1, rate2 = 15, 10
    exposure=1
    low = 1
    diff = rate1 - rate2
    pow_ = power_poisson_diff_2indep(
        diff, rate2, nobs1, nobs_ratio=nobs_ratio, alpha=0.05, value=0,
        alternative='larger', return_results=True)
    assert_allclose(pow_.power, 0.82566, atol=5e-5)
