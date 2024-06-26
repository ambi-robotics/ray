import unittest

import ray
from ray import air, tune
from ray.air.constants import TRAINING_ITERATION
from ray.rllib.utils.framework import try_import_tf
from ray.tune.registry import get_trainable_cls

tf1, tf, tfv = try_import_tf()


def check_support(alg, config, test_eager=False, test_trace=True):
    config["framework"] = "tf2"
    config["log_level"] = "ERROR"
    # Test both continuous and discrete actions.
    for cont in [True, False]:
        if cont and alg == "DQN":
            continue

        if cont:
            config["env"] = "Pendulum-v1"
        else:
            config["env"] = "CartPole-v1"

        a = get_trainable_cls(alg)
        if test_eager:
            print("tf-eager: alg={} cont.act={}".format(alg, cont))
            config["eager_tracing"] = False
            tune.Tuner(
                a,
                param_space=config,
                run_config=air.RunConfig(stop={TRAINING_ITERATION: 1}, verbose=1),
            ).fit()
        if test_trace:
            config["eager_tracing"] = True
            print("tf-eager-tracing: alg={} cont.act={}".format(alg, cont))
            tune.Tuner(
                a,
                param_space=config,
                run_config=air.RunConfig(stop={TRAINING_ITERATION: 1}, verbose=1),
            ).fit()


class TestEagerSupportPolicyGradient(unittest.TestCase):
    def setUp(self):
        ray.init(num_cpus=4)

    def tearDown(self):
        ray.shutdown()

    def test_dqn(self):
        check_support(
            "DQN",
            {
                "num_workers": 0,
                "num_steps_sampled_before_learning_starts": 0,
            },
        )

    def test_ppo(self):
        check_support("PPO", {"num_workers": 0})

    def test_appo(self):
        check_support("APPO", {"num_workers": 1, "num_gpus": 0})

    def test_impala(self):
        check_support("IMPALA", {"num_workers": 1, "num_gpus": 0}, test_eager=True)


class TestEagerSupportOffPolicy(unittest.TestCase):
    def setUp(self):
        ray.init(num_cpus=4)

    def tearDown(self):
        ray.shutdown()

    def test_dqn(self):
        check_support(
            "DQN",
            {
                "num_workers": 0,
                "num_steps_sampled_before_learning_starts": 0,
            },
        )

    def test_sac(self):
        check_support(
            "SAC",
            {
                "num_workers": 0,
                "num_steps_sampled_before_learning_starts": 0,
            },
        )


if __name__ == "__main__":
    import sys

    # Don't test anything for version 2.x (all tests are eager anyways).
    # TODO: (sven) remove entire file in the future.
    if tfv == 2:
        print("\tskip due to tf==2.x")
        sys.exit(0)

    # One can specify the specific TestCase class to run.
    # None for all unittest.TestCase classes in this file.
    import pytest

    class_ = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(pytest.main(["-v", __file__ + ("" if class_ is None else "::" + class_)]))
