class AIEvaluator:

    def evaluate(self, value, evaluation_rule):
        rule = evaluation_rule.replace("count", str(value))

        try:
            if eval(rule):
                return "PASS", f"Control satisfied ({rule})"
            else:
                return "FAIL", f"Control violation ({rule})"
        except Exception as e:
            return "ERROR", str(e)
