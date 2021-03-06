dnl Copyright (C) 2010- Alexey Petrov
dnl Copyright (C) 2009-2010 Pebble Bed Modular Reactor (Pty) Limited (PBMR)
dnl 
dnl This program is free software: you can redistribute it and/or modify
dnl it under the terms of the GNU General Public License as published by
dnl the Free Software Foundation, either version 3 of the License, or
dnl (at your option) any later version.
dnl
dnl This program is distributed in the hope that it will be useful,
dnl but WITHOUT ANY WARRANTY; without even the implied warranty of
dnl MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
dnl GNU General Public License for more details.
dnl 
dnl You should have received a copy of the GNU General Public License
dnl along with this program.  If not, see <http://www.gnu.org/licenses/>.
dnl 
dnl See http://sourceforge.net/projects/pythonflu
dnl
dnl Author : Alexey PETROV
dnl


dnl --------------------------------------------------------------------------------
AC_DEFUN([HYBRIDFLU_CHECK_SOLVER],
[

solver_name=$1

AC_CHECKING(for ${solver_name} package)

eval ${solver_name}_ok=no

dnl --------------------------------------------------------------------------------
AC_CHECK_PROG( [solver_exe], [${solver_name}], [yes], [no] )

check_solver=[`python -c "import ${solver_name}; print \"ok\"" 2>/dev/null`]

if test "${check_solver}" == "ok" && test "${solver_exe}" == "yes"; then
    eval ${solver_name}_ok=yes
fi


dnl --------------------------------------------------------------------------------
])


dnl --------------------------------------------------------------------------------
