! lorentz.f90 — Knotenweise Volumenlast (Lorentzkraftdichte J x B, N/m^3) aus Datei fuer StressSolve.
!
! Uebersetzen:  elmerf90 -o lorentz.so lorentz.f90
! Im sif:       Stress Bodyforce 1 = Variable Time
!                 Real Procedure "<pfad>/lorentz.so" "kraft_x"     (kraft_y, kraft_z entsprechend)
! Datei kraft.dat im Fallordner: erste Zeile Knotenzahl, dann je Knoten  x y z fx fy fz
! (Reihenfolge wie mesh.nodes). Beim ersten Aufruf wird gelesen und gegen die Netzkoordinaten
! geprueft -> Abbruch, falls Elmer die Knoten anders nummeriert als die Datei.
MODULE lorentz_daten
  USE Types
  IMPLICIT NONE
  REAL(KIND=dp), ALLOCATABLE :: KRAFT(:,:)
  LOGICAL :: geladen = .FALSE.
CONTAINS
  SUBROUTINE laden(Model)
    USE DefUtils
    TYPE(Model_t) :: Model
    INTEGER :: N, i, u
    REAL(KIND=dp) :: x(3), d
    OPEN(NEWUNIT=u, FILE='kraft.dat', STATUS='OLD', ACTION='READ')
    READ(u, *) N
    IF (N /= Model % Mesh % NumberOfNodes) CALL Fatal('lorentz', 'Knotenzahl in kraft.dat passt nicht zum Netz')
    ALLOCATE(KRAFT(3, N))
    d = 0.0_dp
    DO i = 1, N
      READ(u, *) x, KRAFT(:, i)
      d = MAX(d, ABS(x(1) - Model % Mesh % Nodes % x(i)) + ABS(x(2) - Model % Mesh % Nodes % y(i)) &
                 + ABS(x(3) - Model % Mesh % Nodes % z(i)))
    END DO
    CLOSE(u)
    IF (d > 1.0e-6_dp) CALL Fatal('lorentz', 'Knotenreihenfolge in kraft.dat passt nicht zum Netz')
    CALL Info('lorentz', 'kraft.dat gelesen, Knoten passen', Level=4)
    geladen = .TRUE.
  END SUBROUTINE laden
END MODULE lorentz_daten

FUNCTION kraft_x(Model, n, t) RESULT(f)
  USE DefUtils
  USE lorentz_daten
  TYPE(Model_t) :: Model
  INTEGER :: n
  REAL(KIND=dp) :: t, f
  IF (.NOT. geladen) CALL laden(Model)
  f = KRAFT(1, n)
END FUNCTION kraft_x

FUNCTION kraft_y(Model, n, t) RESULT(f)
  USE DefUtils
  USE lorentz_daten
  TYPE(Model_t) :: Model
  INTEGER :: n
  REAL(KIND=dp) :: t, f
  IF (.NOT. geladen) CALL laden(Model)
  f = KRAFT(2, n)
END FUNCTION kraft_y

FUNCTION kraft_z(Model, n, t) RESULT(f)
  USE DefUtils
  USE lorentz_daten
  TYPE(Model_t) :: Model
  INTEGER :: n
  REAL(KIND=dp) :: t, f
  IF (.NOT. geladen) CALL laden(Model)
  f = KRAFT(3, n)
END FUNCTION kraft_z
