# orcamento_aluguel.py
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from typing import Optional


def brl(valor: float) -> str:
    """Formata valor em BRL simples (ex.: 1200.5 -> 'R$ 1.200,50')."""
    s = f"{valor:,.2f}"
    # troca separadores para padrão BR
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


@dataclass(frozen=True)
class Orcamento:
    tipo_imovel: str
    quartos: int
    tem_garagem: bool
    criancas: Optional[bool]  # só importa para apartamento
    vagas_estudio: int        # só importa para estúdio
    aluguel_mensal: float
    contrato_total: float
    contrato_parcelas: int

    @property
    def valor_contrato_parcela(self) -> float:
        return self.contrato_total / self.contrato_parcelas

    def resumo(self) -> str:
        linhas = [
            "==== RESUMO DO ORÇAMENTO ====",
            f"Tipo do imóvel: {self.tipo_imovel}",
            f"Quartos: {self.quartos}" if self.tipo_imovel != "Estudio" else "Quartos: (não aplicável)",
        ]

        if self.tipo_imovel in ("Apartamento", "Casa"):
            linhas.append(f"Garagem: {'Sim' if self.tem_garagem else 'Não'}")

        if self.tipo_imovel == "Apartamento" and self.criancas is not None:
            linhas.append(f"Possui crianças: {'Sim' if self.criancas else 'Não'}")

        if self.tipo_imovel == "Estudio":
            linhas.append(f"Vagas (estacionamento): {self.vagas_estudio}")

        linhas += [
            f"Aluguel mensal orçado: {brl(self.aluguel_mensal)}",
            f"Contrato imobiliário: {brl(self.contrato_total)}",
            f"Parcelamento do contrato: {self.contrato_parcelas}x de {brl(self.valor_contrato_parcela)}",
            "=============================",
        ]
        return "\n".join(linhas)


class CalculadoraAluguel:
    # Valores padrões (requisito)
    VALOR_APARTAMENTO_1Q = 700.00
    VALOR_CASA_1Q = 900.00
    VALOR_ESTUDIO = 1200.00

    # Contrato (requisito)
    CONTRATO_TOTAL = 2000.00
    MAX_PARCELAS_CONTRATO = 5

    # Regras adicionais (requisito)
    ADIC_APTO_2Q = 200.00
    ADIC_CASA_2Q = 250.00
    ADIC_GARAGEM_APTO_CASA = 300.00

    # Estúdio: 2 vagas = 250; cada vaga extra = 60
    ESTUDIO_2_VAGAS_VALOR = 250.00
    ESTUDIO_VAGA_EXTRA_VALOR = 60.00
    ESTUDIO_VAGAS_MIN = 0  # o enunciado diz "pode ser adicionado", então deixo 0 permitido

    # Desconto 5% para apartamento sem crianças
    DESCONTO_APTO_SEM_CRIANCAS = 0.05

    def calcular(self,
                 tipo_imovel: str,
                 quartos: int = 1,
                 tem_garagem: bool = False,
                 possui_criancas: Optional[bool] = None,
                 vagas_estudio: int = 0,
                 parcelas_contrato: int = 1) -> Orcamento:

        tipo = self._normalizar_tipo(tipo_imovel)
        parcelas = self._validar_parcelas(parcelas_contrato)

        if tipo == "Apartamento":
            aluguel = self._calc_apartamento(quartos, tem_garagem, possui_criancas)
            return Orcamento(
                tipo_imovel=tipo,
                quartos=quartos,
                tem_garagem=tem_garagem,
                criancas=possui_criancas,
                vagas_estudio=0,
                aluguel_mensal=aluguel,
                contrato_total=self.CONTRATO_TOTAL,
                contrato_parcelas=parcelas
            )

        if tipo == "Casa":
            aluguel = self._calc_casa(quartos, tem_garagem)
            return Orcamento(
                tipo_imovel=tipo,
                quartos=quartos,
                tem_garagem=tem_garagem,
                criancas=None,
                vagas_estudio=0,
                aluguel_mensal=aluguel,
                contrato_total=self.CONTRATO_TOTAL,
                contrato_parcelas=parcelas
            )

        # Estudio
        aluguel = self._calc_estudio(vagas_estudio)
        return Orcamento(
            tipo_imovel=tipo,
            quartos=0,
            tem_garagem=False,
            criancas=None,
            vagas_estudio=vagas_estudio,
            aluguel_mensal=aluguel,
            contrato_total=self.CONTRATO_TOTAL,
            contrato_parcelas=parcelas
        )

    def _normalizar_tipo(self, tipo: str) -> str:
        t = (tipo or "").strip().lower()
        if t in ("apartamento", "apto"):
            return "Apartamento"
        if t in ("casa",):
            return "Casa"
        if t in ("estudio", "estúdio", "studio"):
            return "Estudio"
        raise ValueError("Tipo inválido. Use: Apartamento, Casa ou Estudio.")

    def _validar_parcelas(self, parcelas: int) -> int:
        if not isinstance(parcelas, int):
            raise ValueError("Parcelas do contrato deve ser um número inteiro.")
        if parcelas < 1 or parcelas > self.MAX_PARCELAS_CONTRATO:
            raise ValueError(f"Parcelas do contrato deve ser entre 1 e {self.MAX_PARCELAS_CONTRATO}.")
        return parcelas

    def _calc_apartamento(self, quartos: int, tem_garagem: bool, possui_criancas: Optional[bool]) -> float:
        if quartos not in (1, 2):
            raise ValueError("Apartamento: quartos deve ser 1 ou 2.")
        aluguel = self.VALOR_APARTAMENTO_1Q
        if quartos == 2:
            aluguel += self.ADIC_APTO_2Q
        if tem_garagem:
            aluguel += self.ADIC_GARAGEM_APTO_CASA

        # desconto 5% para apartamento sem crianças
        # (só aplica se o usuário respondeu explicitamente)
        if possui_criancas is False:
            aluguel *= (1 - self.DESCONTO_APTO_SEM_CRIANCAS)

        return aluguel

    def _calc_casa(self, quartos: int, tem_garagem: bool) -> float:
        if quartos not in (1, 2):
            raise ValueError("Casa: quartos deve ser 1 ou 2.")
        aluguel = self.VALOR_CASA_1Q
        if quartos == 2:
            aluguel += self.ADIC_CASA_2Q
        if tem_garagem:
            aluguel += self.ADIC_GARAGEM_APTO_CASA
        return aluguel

    def _calc_estudio(self, vagas: int) -> float:
        if not isinstance(vagas, int) or vagas < self.ESTUDIO_VAGAS_MIN:
            raise ValueError("Estudio: vagas deve ser um inteiro >= 0.")

        aluguel = self.VALOR_ESTUDIO
        if vagas == 0:
            return aluguel

        # 2 vagas custam 250 (quando adicionadas)
        # Se usuário pedir 1 vaga, assumimos que entra no pacote mínimo de 2 (requisito fala em 2 vagas)
        if vagas <= 2:
            aluguel += self.ESTUDIO_2_VAGAS_VALOR
            return aluguel

        # vagas > 2: 2 vagas = 250, extras = 60 cada
        extras = vagas - 2
        aluguel += self.ESTUDIO_2_VAGAS_VALOR + (extras * self.ESTUDIO_VAGA_EXTRA_VALOR)
        return aluguel


class ExportadorCSV:
    """Gera o arquivo CSV com 12 parcelas do orçamento (mensalidade + parcela do contrato)."""

    @staticmethod
    def exportar_12_parcelas(orc: Orcamento, caminho_arquivo: str) -> None:
        hoje = date.today()
        valor_contrato_parcela = orc.valor_contrato_parcela

        # Para as 12 parcelas do orçamento:
        # - Aluguel sempre entra
        # - Contrato entra somente nas primeiras N parcelas (até 5), depois 0
        linhas = []
        for i in range(1, 13):
            contrato_esta_parcela = valor_contrato_parcela if i <= orc.contrato_parcelas else 0.0
            total_mes = orc.aluguel_mensal + contrato_esta_parcela
            linhas.append({
                "parcela": i,
                "aluguel_mensal": f"{orc.aluguel_mensal:.2f}",
                "contrato_parcela": f"{contrato_esta_parcela:.2f}",
                "total_mes": f"{total_mes:.2f}",
                "data_referencia": f"{hoje.year}-{hoje.month:02d}"
            })

        with open(caminho_arquivo, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["parcela", "aluguel_mensal", "contrato_parcela", "total_mes", "data_referencia"],
                delimiter=";"
            )
            writer.writeheader()
            writer.writerows(linhas)


def _ler_int(msg: str, validos: Optional[set[int]] = None, minimo: Optional[int] = None) -> int:
    while True:
        try:
            v = int(input(msg).strip())
            if validos is not None and v not in validos:
                print(f"Valor inválido. Opções: {sorted(validos)}")
                continue
            if minimo is not None and v < minimo:
                print(f"Valor inválido. Deve ser >= {minimo}.")
                continue
            return v
        except ValueError:
            print("Digite um número inteiro válido.")


def _ler_bool(msg: str) -> bool:
    while True:
        v = input(msg + " (s/n): ").strip().lower()
        if v in ("s", "sim"):
            return True
        if v in ("n", "nao", "não"):
            return False
        print("Resposta inválida. Digite 's' ou 'n'.")


def main() -> None:
    print("=== Sistema de Orçamento de Aluguel (R.M) ===")
    print("Tipos disponíveis: Apartamento, Casa, Estudio")

    tipo = input("Informe o tipo do imóvel: ").strip()
    calc = CalculadoraAluguel()

    tipo_norm = None
    try:
        tipo_norm = calc._normalizar_tipo(tipo)
    except ValueError as e:
        print(f"Erro: {e}")
        return

    quartos = 1
    tem_garagem = False
    possui_criancas: Optional[bool] = None
    vagas_estudio = 0

    if tipo_norm in ("Apartamento", "Casa"):
        quartos = _ler_int("Quantidade de quartos (1 ou 2): ", validos={1, 2})
        tem_garagem = _ler_bool("Deseja incluir vaga de garagem?")
        if tipo_norm == "Apartamento":
            possui_criancas = _ler_bool("Possui crianças?")

    if tipo_norm == "Estudio":
        vagas_estudio = _ler_int("Quantas vagas de estacionamento deseja adicionar? (0 para nenhuma): ", minimo=0)

    parcelas_contrato = _ler_int("Em quantas vezes deseja parcelar o contrato? (1 a 5): ", validos={1, 2, 3, 4, 5})

    try:
        orc = calc.calcular(
            tipo_imovel=tipo_norm,
            quartos=quartos,
            tem_garagem=tem_garagem,
            possui_criancas=possui_criancas,
            vagas_estudio=vagas_estudio,
            parcelas_contrato=parcelas_contrato
        )
    except ValueError as e:
        print(f"Erro: {e}")
        return

    print()
    print(orc.resumo())

    print()
    if _ler_bool("Deseja gerar o arquivo CSV com as 12 parcelas do orçamento?"):
        nome = input("Nome do arquivo (ex: parcelas.csv): ").strip()
        if not nome.lower().endswith(".csv"):
            nome += ".csv"
        try:
            ExportadorCSV.exportar_12_parcelas(orc, nome)
            print(f"CSV gerado com sucesso: {nome}")
        except OSError as e:
            print(f"Falha ao gerar CSV: {e}")


if __name__ == "__main__":
    main()
