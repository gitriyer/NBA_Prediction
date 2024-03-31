import pandas as pd

df = pd.read_csv("nba_games.csv", index_col=0)
df = df.sort_values("date")
df = df.reset_index(drop=True)

del df["mp.1"]
del df["mp_opp.1"]
del df["index_opp"]


def add_target(group):
    group["target"] = group["won"].shift(-1)
    return group


df = df.groupby("team", group_keys=False).apply(add_target)

df["target"][pd.isnull(df["target"])] = 2
df["target"] = df["target"].astype(int, errors="ignore")

nulls = pd.isnull(df).sum()
nulls = nulls[nulls > 0]

valid_columns = df.columns[~df.columns.isin(nulls.index)]

df = df[valid_columns].copy()

from sklearn.linear_model import RidgeClassifier
from sklearn.feature_selection import SequentialFeatureSelector
from sklearn.model_selection import TimeSeriesSplit

rr = RidgeClassifier(alpha=1)

split = TimeSeriesSplit(n_splits=5)

sfs = SequentialFeatureSelector(rr,
                                n_features_to_select=30,
                                direction="backward",
                                cv=split,
                                n_jobs=1
                                )

removed_columns = ["season", "date", "won", "target", "team", "team_opp"]
selected_columns = df.columns[~df.columns.isin(removed_columns)]

from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
df[selected_columns] = scaler.fit_transform(df[selected_columns])

sfs.fit(df[selected_columns], df["target"])

predictors = list(selected_columns[sfs.get_support()])


def backtest(data, model, predictors, start=2, step=1):
    all_predictions = []

    seasons = sorted(data["season"].unique())

    for i in range(start, len(seasons), step):
        season = seasons[i]
        train = data[data["season"] < season]
        test = data[data["season"] == season]

        model.fit(train[predictors], train["target"])

        preds = model.predict(test[predictors])
        preds = pd.Series(preds, index=test.index)
        combined = pd.concat([test["target"], preds], axis=1)
        combined.columns = ["actual", "prediction"]

        all_predictions.append(combined)
    return pd.concat(all_predictions)


predictions = backtest(df, rr, predictors)

from sklearn.metrics import accuracy_score

accuracy_score(predictions["actual"], predictions["prediction"])
